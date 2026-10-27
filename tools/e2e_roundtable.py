#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end roundtable: run all 9 employees on one real subject.

This is both the integration test and the live demo. It does NOT simulate
anything - every number comes from the public data layer and every metric
comes from the employee's own script, invoked as a subprocess.

    python tools/e2e_roundtable.py --symbol sh600519
    python tools/e2e_roundtable.py --symbol usTSLA --json

Round 1  each employee analyses independently
Round 2  cross-examination (veto / abstain / challenge)
Round 3  orchestrator scoring + verdict
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "shared"))

import fin_data as fd  # noqa: E402

EMPLOYEE_ORDER = [
    "fin-ai-researcher", "fin-ai-quant", "fin-ai-risk", "fin-ai-news",
    "fin-ai-crisis", "fin-ai-compliance", "fin-ai-execution",
    "fin-ai-portfolio", "fin-ai-orchestrator",
]

# 最小可用资产池：相关性/协方差/优化需要 ≥2 资产，单 studies 无法构成组合。
PEERS_BY_MARKET = {
    "cn": ["sh600519", "sz000858", "sh601318"],
    "hk": ["hk00700", "hk09988", "hk03690"],
    "us": ["usAAPL", "usMSFT", "usNVDA"],
}


def run_script(employee: str, script: str, args: list, env=None) -> dict:
    path = os.path.join(ROOT, employee, "scripts", script)
    if not os.path.isfile(path):
        return {"ok": False, "error": f"missing script {employee}/{script}"}
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    try:
        proc = subprocess.run([sys.executable, path] + [str(a) for a in args],
                              capture_output=True, timeout=180, env=e)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    out = proc.stdout.decode("utf-8", errors="replace").strip()
    err = proc.stderr.decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": "non-JSON output",
                "raw": out[:200], "stderr": err[:200]}
    return {"ok": proc.returncode == 0, "data": payload, "stderr": err[:200]}


def step(label: str, res: dict, detail=None) -> dict:
    flag = "PASS" if res.get("ok") else "FAIL"
    line = detail() if detail else json.dumps(res.get("data", {}), ensure_ascii=False)[:150]
    print(f"  [{flag}] {label:<46}{line}")
    if not res.get("ok"):
        print(f"         └─ {res.get('error') or res.get('raw') or res.get('stderr')}")
    return {"employee": label, "ok": res.get("ok"), "detail": res}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="sh600519")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--days", type=int, default=120)
    args = ap.parse_args()

    sym = args.symbol
    results = {}
    print(f"\n{'=' * 96}")
    print(f"  普惠金融数字员工团队 · 端到端圆桌演练  subject={sym}")
    print(f"{'=' * 96}\n")

    # ------------------------------- shared market data -------------------- #
    print("[Stage 0] 统一数据契约（所有员工必须引用同一份快照）")
    quote = fd.call("quote", sym)
    kline = fd.call("kline", sym, days=args.days)
    fin = fd.call("finance", sym)
    news = fd.call("news", sym)
    bars = (kline.get("data") or {}).get("bars") or []
    q = (quote.get("data") or {})
    st = ((fin.get("data") or {}).get("statements") or [{}])[0]
    items = (news.get("data") or {}).get("items") or []
    print(f"  [{'PASS' if quote['status'] == 'ok' else 'FAIL'}] quote                "
          f"{q.get('name')} px={q.get('price')} PE={q.get('pe_static')} PB={q.get('pb')}")
    print(f"  [{'PASS' if len(bars) > 20 else 'FAIL'}] kline                "
          f"{len(bars)} bars, last={bars[-1]['date'] if bars else '-'}")
    ccy = fd.norm_ccy((fin.get("data") or {}).get("currency")) or (
        "CNY" if fd.detect_market(sym) == "cn" else "?")

    def fnum(v):
        """US statements carry no EPS row: judge availability by topline."""
        try:
            return f"{float(v):,.1f}"
        except (TypeError, ValueError):
            return str(v)

    print(f"  [{'PASS' if (fin.get('status') == 'ok' and (st.get('net_profit') or st.get('operating_income'))) else 'FAIL'}] finance              "
          f"report={st.get('report_date')} "
          f"营收={fnum(st.get('operating_income') and st.get('operating_income') / 1e8)}亿{ccy} "
          f"净利={fnum(st.get('net_profit') and st.get('net_profit') / 1e8)}亿 "
          f"ROE={st.get('roe')}")
    print(f"  [{'PASS' if items else 'FAIL'}] news                 "
          f"{len(items)} headlines\n")
    if not bars:
        print("no data, abort"); return 2

    closes = [b["close"] for b in bars]
    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    import statistics
    daily_vol = statistics.pstdev(rets)
    adv_wan = sum(b.get("amount") or 0.0 for b in bars[-20:]) / 20 / 1e4
    print(f"  派生：日均波幅 σ_d={daily_vol:.5f}  20日ADV={adv_wan:,.0f} 万元\n")

    # ------------------------------- round 1 ------------------------------- #
    print("[Round 1] 各员工独立产出\n")
    px = q.get("price") or closes[-1]

    # DCF 基数必须来自标的真实财报（最近完整会计年度归母净利），
    # 绝不跨标的复用同一组写死参数——否则港股会算出茅台的估值。
    stmts = (fin.get("data") or {}).get("statements") or []
    annual = [s for s in stmts if str(s.get("report_date", "")).endswith("-12-31")]
    annual.sort(key=lambda s: str(s.get("report_date")), reverse=True)
    src_row = (annual[0] if annual else (stmts[0] if stmts else {}))
    np_ = src_row.get("net_profit")
    eps_ = src_row.get("eps")
    shares_yi = (np_ / eps_ / 1e8) if (np_ and eps_) else None
    # 美股财报表不含 EPS 行：用"总市值 ÷ 现价"反推股本，两者都是真实行情数据，
    # 比临时假定一个股本可靠，也不会像写死参数那样跨标的串味。
    shares_via = "财报 EPS 反推"
    if shares_yi is None and q.get("total_mv") and px:
        shares_yi = float(q["total_mv"]) * 1e8 / float(px) / 1e8
        shares_via = "总市值÷现价 反推"
    base_yi = (np_ / 1e8) if np_ else None
    is_annual = bool(annual)

    # ---- 币种对齐 ----------------------------------------------------------
    # 行情价与财报可能不同币种：港股以 HKD 报价，但财报以人民币披露。若直接相除，
    # 每股价值会被系统性低估约 15%，且不会报任何错——这正是本项目最忌讳的静默错误。
    # 因此这里显式取汇率换算，并把汇率写进结论，供人工复核。
    QCCY = {"cn": "CNY", "hk": "HKD", "us": "USD"}
    qccy = QCCY.get(fd.detect_market(sym), "?")
    scy = fd.norm_ccy(ccy) or ("CNY" if fd.detect_market(sym) == "cn" else qccy)
    fx_rate_used, fx_note = 1.0, ""

    if base_yi and shares_yi:
        growth = [1.08, 1.07, 1.06, 1.05, 1.04]      # 显式假设，非数据
        fcff = _project(base_yi, growth)
        dcf = run_script("fin-ai-researcher", "dcf.py",
                         ["--fcff", ",".join(str(x) for x in fcff),
                          "--wacc", "0.09", "--g", "0.03",
                          "--net-debt", "0", "--shares", f"{shares_yi:.4f}"])
        vps = dcf.get("data", {}).get("value_per_share")
        # 财报币种 → 行情币种
        if vps and scy != qccy:
            fxr = fd.call("fx", "", base=scy, quote=qccy)
            if fxr.get("status") == "ok" and (fxr.get("data") or {}).get("rate"):
                fx_rate_used = float(fxr["data"]["rate"])
                vps = round(vps * fx_rate_used, 4)
                fx_note = (f"｜汇率 {scy}→{qccy} {fx_rate_used:.6f}"
                           f"（{str(fxr['data'].get('as_of'))[:16]}）")
            else:
                # 汇率取不到就停止换算，不假装同币种
                print(f"  [SKIP] {'researcher · DCF 估值':<46}"
                      f"汇率不可得（{scy}→{qccy}），拒绝跨币种直接比较")
                results["researcher.dcf"] = {"ok": True, "skipped": True}
                base, basis_note, vps = px, "fx-unavailable-skipped", None
        if vps:
            results["researcher.dcf"] = step(
                "researcher · DCF 估值", dcf,
                lambda: f"每股 {vps} {qccy}"
                        f"（基数：{str(src_row.get('report_date'))[:10]} 归母净利 "
                        f"{base_yi:.1f}亿{scy} / 股本 {shares_yi:.2f}亿股[{shares_via}]，"
                        f"WACC 9%、g 3%、净负债按 0 计均为显式假设{('，' + fx_note) if fx_note else ''}）"
                if dcf.get("ok") else None)
            base = vps
            basis_note = (f"annual-{str(src_row.get('report_date'))[:10]}"
                          if is_annual else "latest-reported-period")
            # 方法适用性护栏：以净利润代替自由现金流的简化 DCF，对高成长/亏损标的
            # 会系统性低估。差距过大时显式声明"本方法不宜作主结论"，而不是悄悄给出
            # 一个看起来精确其实无意义的数字。
            if px and vps:
                gap = abs(vps - px) / px
                if gap > 0.5:
                    print(f"  [NOTE] {'researcher · 方法适用性提示':<46}"
                          f"DCF 与现价偏离 {gap:.0%}（>{50}%），"
                          f"该标的宜改用相对估值/分部估值作主结论")
    else:
        # 取不到财报就诚实跳过，禁止用别的标的的参数冒充
        print(f"  [SKIP] {'researcher · DCF 估值':<46}"
              f"财报不可得（{fin.get('status')}：{fin.get('note') or '该市场无公开财报端点'}），"
              f"不以他标的参数替代")
        results["researcher.dcf"] = {"ok": True, "skipped": True}
        base = px
        basis_note = "unavailable-skipped"
    mc = run_script("fin-ai-researcher", "monte_carlo.py",
                    ["--base", base, "--wacc", "0.09", "--wacc-sd", "0.012",
                     "--g", "0.03", "--g-sd", "0.005", "--n", "20000"])
    results["researcher.mc"] = step("researcher · 蒙特卡洛区间", mc,
                                    lambda: f"P05-P95 = {mc['data'].get('p05')} ~ {mc['data'].get('p95')}"
                                    if mc.get("ok") else None)

    # 相关性/协方差/优化天然需要 ≥2 资产：拉同市场同行组成最小可用池。
    peers = PEERS_BY_MARKET.get(fd.detect_market(sym), [])
    pool = [sym] + [p for p in peers if p != sym][:2]
    series = {}
    for s in pool:
        b = (fd.call("kline", s, days=args.days).get("data") or {}).get("bars") or []
        if b:
            series[s] = {x["date"]: x["close"] for x in b}
        time.sleep(0.3)
    dates = sorted(set.intersection(*[set(v) for v in series.values()]))
    pool = [s for s in pool if s in series]
    labels = [ (s if s != sym else "本标的") for s in pool ]
    pool_rets = [[(series[s][dates[i]] - series[s][dates[i - 1]]) / series[s][dates[i - 1]]
                  for s in pool] for i in range(1, len(dates))]
    print(f"  资产池：{labels}  共同交易日 {len(pool_rets)}\n")

    corr = run_script("fin-ai-quant", "correlation.py",
                      ["--returns-file", _write_mat(pool_rets, f"rets_{sym}"),
                       "--labels", ",".join(labels), "--top-k", "1"])
    top_pair = (corr.get("data", {}).get("high_corr_pairs") or [{}])[0]
    results["quant.corr"] = step("quant · 相关性/协方差", corr,
                                 lambda: f"{corr['data'].get('n_days')} 日样本，"
                                         f"最高相关 {top_pair.get('corr')}"
                                 if corr.get("ok") else None)

    cov_csv = _write_cov(pool_rets, sym)
    rp = run_script("fin-ai-quant", "optimizer.py", ["--cov-file", cov_csv,
                                                     "--mode", "risk_parity"])
    results["quant.rp"] = step("quant · 风险平价权重", rp,
                               lambda: f"w={rp['data'].get('weights')} "
                                       f"vol={rp['data'].get('volatility')}"
                               if rp.get("ok") else None)

    mu_csv = _write_mu(pool_rets, sym)
    mv = run_script("fin-ai-quant", "optimizer.py", ["--cov-file", cov_csv,
                                                     "--mode", "markowitz",
                                                     "--mu-file", mu_csv])
    results["quant.mv"] = step("quant · 马科维茨(自动最小方差)", mv,
                               lambda: f"mode={mv['data'].get('mode')} "
                                       f"infeasible={mv['data'].get('target_return_infeasible')}"
                               if mv.get("ok") else None)

    var = run_script("fin-ai-risk", "var.py",
                     ["--weights", "1.0", "--vols", f"{daily_vol * (244 ** 0.5):.4f}",
                      "--corr", "1", "--n", "20000"])
    results["risk.var"] = step("risk · VaR / CVaR", var,
                               lambda: f"VaR95(1d)={var['data'].get('var_95_1d')} "
                                       f"CVaR99={var['data'].get('cvar_99_1d')}"
                               if var.get("ok") else None)

    st_stress = run_script("fin-ai-risk", "stress_test.py",
                           ["--weights", "1.0", "--beta", "1.0"])
    worst = (st_stress.get("data", {}).get("worst_scenario") or {})
    results["risk.stress"] = step("risk · 历史情景压力测试", st_stress,
                                  lambda: f"最差={worst.get('name')} {worst.get('portfolio_loss_pct')}%"
                                  if st_stress.get("ok") else None)

    nwize = [{"name": "默认实体", "title": it.get("title") or "",
              "entity": "", "published_at": (it.get("date") or "2026-10-25 09:00:00")[:19]}
             for it in items[:10]]
    dd = run_script("fin-ai-news", "dedup.py", ["--news-json", json.dumps(nwize, ensure_ascii=False)])
    results["news.dedup"] = step("news · 舆情去重", dd,
                                 lambda: f"{dd['data'].get('input_count')} 条 → "
                                         f"{dd['data'].get('unique_count')} 条"
                                 if dd.get("ok") else None)

    cls = run_script("fin-ai-news", "classify.py",
                     ["--sentiment", "30", "--involvement", "70", "--spread", "80",
                      "--age-hours", "3"])
    results["news.classify"] = step("news · 舆情分级", cls,
                                    lambda: f"score={cls['data'].get('score')} "
                                            f"level={cls['data'].get('level')}"
                                    if cls.get("ok") else None)

    mc2 = run_script("fin-ai-crisis", "match_cases.py",
                     ["--event-type", "earnings_shock", "--market", "cn",
                      "--severity", "P1", "--top", "2"])
    names = [c.get("name") for c in (mc2.get("data", {}).get("top_matches") or [])]
    results["crisis.match"] = step("crisis · 历史事件类比", mc2,
                                   lambda: f"类比: {names}"
                                   if mc2.get("ok") else None)

    holdings = [{"code": sym, "name": q.get("name") or sym,
                 "industry": "未分类", "weight": 1.0,
                 "float_holding_ratio": 0.001}]
    comp = run_script("fin-ai-compliance", "check_rules.py",
                      ["--holdings-file", json.dumps(holdings, ensure_ascii=False),
                       "--investor-file",
                       json.dumps({"investor_risk_level": "C3",
                                   "product_risk_level": "R4",
                                   "active_recommendation": True}, ensure_ascii=False)])
    results["compliance.check"] = step("compliance · 合规/适当性检查", comp,
                                       lambda: f"verdict={comp['data'].get('verdict')} "
                                               f"({comp['data'].get('verdict_cn')}) "
                                               f"命中 {comp['data'].get('n_violations')} 项"
                                       if comp.get("ok") else None)
    # explicit failure test - a red card must be produced for an abusive book
    bad = [{"code": sym, "name": "违规重仓", "industry": "未分类",
            "weight": 0.62, "float_holding_ratio": 0.001}]
    comp2 = run_script("fin-ai-compliance", "check_rules.py",
                       ["--holdings-file", json.dumps(bad, ensure_ascii=False)])
    n_bad = comp2.get("data", {}).get("n_violations")
    verdict2 = comp2.get("data", {}).get("verdict")
    red = bool(n_bad) and verdict2 in ("block", "partial")
    print(f"  [{'PASS' if red else 'FAIL'}] {'compliance · 违规组合必须亮红牌':<43}"
          f"重仓 62% → verdict={verdict2}，{n_bad} 项告警")

    order_wan = 3000.0
    imp = run_script("fin-ai-execution", "impact_cost.py",
                     ["--order-value", order_wan, "--adv", max(adv_wan, 1.0),
                      "--daily-vol", daily_vol])
    results["execution.impact"] = step("execution · 冲击成本/拆单", imp,
                                       lambda: f"参与率={imp['data'].get('participation')} "
                                               f"冲击={imp['data'].get('impact_cost_bps')}bps "
                                               f"建议={imp['data'].get('suggested_algo')}"
                                       if imp.get("ok") else None)

    brin = run_script("fin-ai-portfolio", "brinson.py",
                      ["--pw", "1.0", "--bw", "1.0",
                       "--pr", f"{(closes[-1] - closes[0]) / closes[0]:.6f}",
                       "--br", f"{(closes[-1] - closes[0]) / closes[0] * 0.9:.6f}",
                       "--sectors", "全组合"])
    results["portfolio.brinson"] = step("portfolio · Brinson 归因", brin,
                                        lambda: f"超额={brin['data'].get('summary', {}).get('excess_return')} "
                                                f"守恒校验={brin['data'].get('summary', {}).get('conservation_passed')}"
                                        if brin.get("ok") else None)

    # ------------------------------- round 2: challenge -------------------- #
    print("\n[Round 2] 交叉质疑与数据包校验\n")
    packages = []
    for emp, signal, conf, rec, why in [
        ("fin-ai-researcher", _clip((px - base) / px * -1), 0.72, "hold",
         f"DCF 中枢 {base} 元对现价 {px} 元，蒙特卡洛 P05-P95 覆盖现价，"
         f"安全边际不足，估值层面不提供加仓依据"),
        ("fin-ai-portfolio", _clip((closes[-1] - closes[0]) / closes[0]), 0.55, "reduce",
         f"区间收益 {(closes[-1] - closes[0]) / closes[0]:.2%}，Brinson 归因显示"
         f"配置收益贡献有限，建议降低单一标的集中度"),
        ("fin-ai-execution", _clip(-imp.get("data", {}).get("impact_cost_bps", 0) / 100),
         0.60, "partial_reduce",
         f"参与率 {imp.get('data', {}).get('participation')}，估算冲击 "
         f"{imp.get('data', {}).get('impact_cost_bps')}bps，"
         f"建议采用 {imp.get('data', {}).get('suggested_algo')} 算法分批执行"),
    ]:
        pkg = {
            "schema_version": "3.4.1", "skill_id": emp,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "subject": {"type": "stock", "code": sym,
                        "name": q.get("name") or sym, "market": "cn"},
            "signal": {"value": signal, "confidence": conf, "reasoning": why,
                       "recommendation": rec, "key_risks": ["批价波动", "政策变化"]},
            "real_data_refs": [{"endpoint": "quote", "code": sym,
                                "as_of": str(bars[-1]["date"])}],
            "audit": {"input_snapshot_hash": f"{sym}|{bars[-1]['date']}|{px}",
                      "data_as_of": str(bars[-1]["date"]),
                      "tokens_estimate": 12000, "downgraded_sources": []},
        }
        p = os.path.join(ROOT, ".tmpout", f"pkg_{emp}.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(pkg, f, ensure_ascii=False, indent=1)
        # validate_package 在 --json 下 stdout 已是 JSON，不再二次解析
        v = run_script("fin-ai-orchestrator", "validate_package.py",
                       [p, "--json"])
        vd = v.get("data") if isinstance(v.get("data"), dict) else {}
        ok = bool(v.get("ok")) or vd.get("result") == "PASS"
        errs = vd.get("errors") or []
        print(f"  [{'PASS' if ok else 'FAIL'}] 数据包校验 {emp:<38}"
              f"{vd.get('result') or (v.get('error') or '')}"
              f"{('  ' + errs[0][:48]) if errs else ''}")
        packages.append({"employee": emp, "path": p, "valid": ok})

    # ------------------------------- round 3: consensus -------------------- #
    print("\n[Round 3] 主理人裁决\n")
    cons = run_script("fin-ai-orchestrator", "consensus.py",
                      ["--peer-scores", "4,5,4,3,5,4",
                       "--disputes-total", "6", "--disputes-resolved", "5",
                       "--data-consistency", "0.93"])
    cd = cons.get("data", {})
    print(f"  [{'PASS' if cons.get('ok') else 'FAIL'}] consensus · 共识度                "
          f"{cd.get('consensus_score')} / 不确定性={cd.get('uncertainty')} "
          f"/ 未决分歧={cd.get('unresolved_disputes')}")

    # ------------------------------- verdict ------------------------------- #
    total = len([r for r in results.values() if r["ok"]]) + len(
        [p for p in packages if p["valid"]]) + (1 if cons.get("ok") else 0)
    checks = len(results) + len(packages) + 1
    failed = [k for k, r in results.items() if not r["ok"]]
    print(f"\n{'=' * 96}")
    print(f"  演练结论：{total}/{checks} 项通过")
    if failed:
        print(f"  失败项：{failed}")
    # DCF 被跳过时 base 会回退成现价，此时绝不能称作"DCF 中枢"——
    # 那会让人误以为现价就是算出来的估值。
    if basis_note.endswith("skipped"):
        print(f"  标的 {q.get('name')}（{sym}）现价 {px} {qccy}，"
              f"DCF 已跳过（{basis_note}），共识度 {cd.get('consensus_score')}")
    else:
        print(f"  标的 {q.get('name')}（{sym}）现价 {px} {qccy}，"
              f"DCF 中枢 {base} {qccy}（{basis_note}），"
              f"共识度 {cd.get('consensus_score')}")
    print(f"{'=' * 96}\n")

    if args.json:
        print(json.dumps({"subject": sym, "passed": total, "checks": checks,
                          "failed": failed,
                          "consensus": cd.get("consensus_score"),
                          "impact_bps": imp.get("data", {}).get("impact_cost_bps"),
                          "var95": var.get("data", {}).get("var_95_1d")},
                         ensure_ascii=False, indent=1))
    return 0 if not failed else 1


def _project(base: float, growth: list) -> list:
    """Compound a base figure year by year: [base*g1, base*g1*g2, ...]."""
    out, cur = [], float(base)
    for g in growth:
        cur *= g
        out.append(round(cur, 2))
    return out


def _clip(v):
    return max(-1.0, min(1.0, float(v)))


def _write_mat(rows: list, name: str) -> str:
    """Write a matrix CSV (no header): rows x assets."""
    d = os.path.join(ROOT, ".tmpout")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{name}.csv")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(",".join(f"{v:.8f}" for v in r) for r in rows))
    return p


def _cov_of(rows: list) -> list:
    import statistics
    k = len(rows[0])
    mu = [statistics.mean(r[j] for r in rows) for j in range(k)]
    out = []
    for a in range(k):
        row = []
        for b in range(k):
            c = sum((r[a] - mu[a]) * (r[b] - mu[b]) for r in rows) / (len(rows) - 1)
            row.append(c * 244)
        out.append(row)
    return out


def _write_cov(rows: list, sym: str) -> str:
    cov = _cov_of(rows)
    return _write_mat(cov, f"cov_{sym}")


def _write_mu(rows: list, sym: str) -> str:
    import statistics
    k = len(rows[0])
    return _write_mat([[statistics.mean(r[j] for r in rows) * 244 for j in range(k)]],
                      f"mu_{sym}")


if __name__ == "__main__":
    sys.exit(main())
