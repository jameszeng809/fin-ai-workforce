#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fin_data.py - Unified Financial Data Layer / 统一金融数据层
============================================================

FinAI Digital Workforce (普惠金融数字员工团队) - shared data layer.

WHY THIS FILE EXISTS
--------------------
The original team was coupled to a proprietary connector (`westock-mcp`).
To make the project usable by anyone in the world, all nine digital employees
now read data through ONE thin layer: this file. It speaks to freely available
public endpoints and needs NO api key.

DATA CHANNELS (three tiers, auto-selected)
------------------------------------------
  L1  Public HTTP endpoints (eastmoney / push2)  -> zero pip install, works everywhere
  L2  AKShare  (optional `pip install akshare`)  -> deep A-share data
  L3  yfinance (optional `pip install yfinance`) -> HK / US equities

If L2/L3 are not installed, L1 still answers. Nothing silently fakes numbers:
every response carries a `status` of ok / degraded / unavailable plus a `note`,
and consumers are required to surface that state in the report (see
DATA_HONESTY contract in README).

CLI
---
    python fin_data.py search 600519
    python fin_data.py quote sh600519 --json
    python fin_data.py kline sh600519 --days 250
    python fin_data.py technical hk00700
    python fin_data.py finance usAAPL
    python fin_data.py fund_flow sh600519
    python fin_data.py list                      # all endpoints

Every endpoint returns a unified envelope:

    {
      "endpoint": "quote",
      "code": "sh600519",
      "resolved": {"secid": "1.600519", "name": "贵州茅台", "market": "cn"},
      "status": "ok",              # ok | degraded | unavailable
      "source": "L1:eastmoney",    # which channel actually answered
      "as_of": "2026-10-25T15:30:00+08:00",
      "data": { ... },
      "note": null,
      "latency_ms": 137
    }

Exit code is always 0 for ok/degraded (so one bad field never kills a pipeline);
it is 2 only for a bad CLI invocation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CN_TZ = timezone(timedelta(hours=8))
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 15

EM_SEARCH_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"


# --------------------------------------------------------------------------- #
# low level helpers
# --------------------------------------------------------------------------- #
# Some Chinese data endpoints reject Python's TLS fingerprint (ClientHello JA3)
# while happily answering curl. So we keep a small transport cascade instead of
# betting on one client. Order: python urllib -> system curl -> give up loudly.
import shutil
import subprocess

CURL_BIN = shutil.which("curl")

_LAST_HIT = [0.0]
MIN_INTERVAL = 0.5          # seconds between network hits, we are polite guests


def _throttle(extra_delay: float = 0.0) -> None:
    wait = MIN_INTERVAL + extra_delay
    elapsed = time.time() - _LAST_HIT[0]
    if 0 < elapsed < wait:
        time.sleep(wait - elapsed)
    _LAST_HIT[0] = time.time()


def _urllib_fetch(url: str, referer: str | None, timeout: int,
                  encoding: str = "utf-8") -> str:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip
            raw = gzip.decompress(raw)
    return raw.decode(encoding, errors="replace")


def _curl_fetch(url: str, referer: str | None, timeout: int,
                encoding: str = "utf-8") -> str:
    if not CURL_BIN:
        raise DataUnavailable("no curl binary available")
    cmd = [CURL_BIN, "-s", "--compressed", "--max-time", str(timeout),
           "-A", UA, "-H", "Accept: */*"]
    if referer:
        cmd += ["-H", f"Referer: {referer}"]
    cmd.append(url)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
    except Exception as exc:
        raise DataUnavailable(f"curl exec failed: {exc}")
    if proc.returncode != 0:
        raise DataUnavailable(f"curl rc={proc.returncode}")
    return proc.stdout.decode(encoding, errors="replace")


class DataUnavailable(Exception):
    """Raised when a channel cannot answer at all."""


def _fetch_raw(url: str, params: dict | None = None, referer: str | None = None,
               timeout: int = TIMEOUT, encoding: str = "utf-8") -> str:
    """GET a URL as text through the transport cascade.

    Cascade (cheapest first, with backoff so we do not trip rate limits):
        urllib -> curl -> [pause 1.2s] -> urllib -> curl
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    plan = [(_urllib_fetch, 0.0), (_curl_fetch, 0.0),
            (_urllib_fetch, 1.2), (_curl_fetch, 1.6)]
    last = None
    for transport, delay in plan:
        _throttle(delay)
        try:
            raw = transport(url, referer, timeout, encoding).strip()
            if not raw:
                raise DataUnavailable("empty response body")
            return raw
        except DataUnavailable as exc:
            last = str(exc)
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    raise DataUnavailable(last or "all transports failed")


def _http(url: str, params: dict | None = None, referer: str | None = None,
          timeout: int = TIMEOUT):
    """GET + JSON.parse via the transport cascade."""
    raw = _fetch_raw(url, params, referer, timeout)
    # jsonp wrapper support:  xxx({"a":1}) / jQuery123({...})
    if raw.startswith(("callback(", "jQuery")):
        i, j = raw.find("("), raw.rfind(")")
        raw = raw[i + 1:j]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DataUnavailable(f"bad json: {exc}, body={raw[:80]!r}")


# --------------------------------------------------------------------------- #
# Tencent finance channel (GBK) - survives where eastmoney's push2his is blocked
# --------------------------------------------------------------------------- #
def tx_symbol(code: str) -> str:
    """sh600519 / hk00700 / usAAPL -> tencent symbol form."""
    c = (code or "").strip().lower()
    if c[:2] in ("sh", "sz", "hk", "us", "bj"):
        return c
    if c.isdigit():
        return c if len(c) == 5 else ("sh" + c if c.startswith(("6", "9")) else "sz" + c)
    return "us" + c.upper()


def tx_quote(code: str, resolved: dict, **kw):
    """Realtime quote via qt.gtimg.cn (GBK, tilde separated)."""
    sym = tx_symbol(code)
    raw = _fetch_raw(f"https://qt.gtimg.cn/q={sym}", encoding="gbk")
    body = None
    for line in raw.split(";"):
        if line.strip().startswith(f"v_{sym}="):
            body = line.partition("=")[2].strip().strip('"')
            break
    if not body:
        raise DataUnavailable(f"tencent quote: no payload for {sym}")
    p = body.split("~")
    if len(p) < 40:
        raise DataUnavailable("tencent quote: truncated payload")

    def f(idx, cast=float):
        try:
            return cast(p[idx])
        except Exception:
            return None

    return {
        "name": p[1], "price": f(3), "prev_close": f(4), "open": f(5),
        "volume": f(6), "change": f(31), "change_pct": f(32),
        "high": f(33), "low": f(34), "amount": f(37),
        "turnover_rate": f(38), "pe_static": f(39), "amplitude": f(43),
        "float_mv": f(44), "total_mv": f(45), "pb": f(46),
        "update_ts": p[30],
        "unit_note": "amount in 万元 (CNY 10k); float_mv/total_mv in 亿元 (CNY 100M)",
    }


def _bars_from_tencent(payload: dict, sym: str) -> list:
    node = (payload.get("data") or {}).get(sym) or {}
    rows = None
    for key in ("qfqday", "hfqday", "day", "week", "month"):
        if node.get(key):
            rows = node[key]
            break
    out = []
    for r in rows or []:
        # [date, open, close, high, low, volume, ...]
        out.append({
            "date": r[0], "open": float(r[1]), "close": float(r[2]),
            "high": float(r[3]), "low": float(r[4]), "volume": float(r[5]),
            "amount": None, "amplitude": None, "chg_pct": None, "chg": None,
            "turnover": None,
        })
    return out


def tx_kline(code: str, resolved: dict, days: int = 250, **kw):
    sym = tx_symbol(code)
    payload = _http(
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
        {"param": f"{sym},day,,,{int(days)},qfq"},
    )
    bars = _bars_from_tencent(payload, sym)
    if not bars:
        raise DataUnavailable(f"tencent kline: empty for {sym}")
    return {"name": resolved.get("name"), "source_detail": "tencent ifzq fqkline",
            "count": len(bars), "bars": bars}


def sina_kline(code: str, resolved: dict, days: int = 250, **kw):
    sym = tx_symbol(code)
    raw = _fetch_raw(
        "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "CN_MarketData.getKLineData",
        {"symbol": sym, "scale": "240", "ma": "no", "datalen": str(int(days))},
        referer="https://finance.sina.com.cn/",
    )
    try:
        rows = json.loads(raw)          # may come back as a JSON object too
    except json.JSONDecodeError:
        raise DataUnavailable("sina kline: bad payload")
    if isinstance(rows, dict):
        rows = rows.get("result", {}).get("data") or []
    out = []
    for r in rows or []:
        out.append({
            "date": r.get("day"), "open": float(r.get("open")),
            "close": float(r.get("close")), "high": float(r.get("high")),
            "low": float(r.get("low")), "volume": float(r.get("volume")),
            "amount": None, "amplitude": None, "chg_pct": None,
            "chg": None, "turnover": None,
        })
    if not out:
        raise DataUnavailable("sina kline: empty")
    return {"name": resolved.get("name"), "source_detail": "sina money api",
            "count": len(out), "bars": out}


INDEX_TARGETS = [("sh000001", "上证指数"), ("sz399001", "深证成指"),
                 ("sz399006", "创业板指"), ("sh000688", "科创50"),
                 ("sh000300", "沪深300"), ("hkHSI", "恒生指数"),
                 ("usDJI", "道琼斯"), ("usIXIC", "纳斯达克")]


def tx_index(code: str = "", resolved: dict | None = None, **kw):
    syms = ",".join(s for s, _ in INDEX_TARGETS)
    raw = _fetch_raw(f"https://qt.gtimg.cn/q={syms}", encoding="gbk")
    labels = dict(INDEX_TARGETS)
    items = []
    for line in raw.split(";"):
        line = line.strip()
        if not line.startswith("v_") or "=" not in line:
            continue
        sym = line[2:line.index("=")]
        p = line.partition("=")[2].strip().strip('"').split("~")
        if len(p) < 33:
            continue
        try:
            items.append({
                "code": sym, "name": p[1] or labels.get(sym, sym),
                "price": float(p[3]), "prev_close": float(p[4]),
                "change": float(p[31]), "chg_pct": float(p[32]),
                "volume": float(p[6]) if p[6] else None,
            })
        except Exception:
            continue
    if not items:
        raise DataUnavailable("tencent index: empty")
    return {"as_of": datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "source_detail": "tencent qt.gtimg.cn", "items": items}


# --------------------------------------------------------------------------- #
# symbol resolution
# --------------------------------------------------------------------------- #
def detect_market(code: str) -> str:
    """sh600519 / hk00700 / usAAPL / 600519 / AAPL -> cn | hk | us"""
    c = (code or "").strip().lower()
    if c.startswith(("sh", "sz", "bj")):
        return "cn"
    if c.startswith("hk"):
        return "hk"
    if c.startswith("us"):
        return "us"
    body = c[2:] if c[:2] in ("sh", "sz", "hk", "us", "bj") else c
    if body.isdigit():
        return "hk" if len(body) == 5 else "cn"
    return "us"


def _cn_prefix(body: str) -> str:
    """600519 -> 1 (Shanghai) / 000001 -> 0 (Shenzhen) / 8xxxxx -> 0 (BSE)"""
    if body.startswith(("6", "9")):
        return "1"
    if body.startswith(("4", "8")):
        return "0"
    return "0"


def secid_of(code: str) -> tuple[str, str]:
    """Return (market, secid). Best-effort offline guess."""
    m = detect_market(code)
    c = (code or "").strip().lower()
    body = c[2:] if c[:2] in ("sh", "sz", "hk", "us", "bj") else c
    if m == "cn":
        return m, f"{_cn_prefix(body)}.{body}"
    if m == "hk":
        return m, f"116.{body.zfill(5)}"
    return m, f"106.{body.upper()}"          # 106 = NYSE guess; search will confirm


def resolve(code: str) -> dict:
    """Resolve a human code to eastmoney metadata using their suggest API."""
    c = (code or "").strip()
    q = c[len(c[:2]):] if c[:2].lower() in ("sh", "sz", "hk", "us", "bj") else c
    try:
        payload = _http(
            "https://searchapi.eastmoney.com/api/suggest/get",
            {"input": q, "type": "14", "token": EM_SEARCH_TOKEN, "count": "8"},
            referer="https://www.eastmoney.com/",
        )
        items = (payload.get("QuotationCodeTable") or {}).get("Data") or []
        if items:
            it = items[0]
            return {
                "secid": f"{it.get('MktNum')}.{it.get('Code')}",
                "name": it.get("Name"),
                "em_code": it.get("Code"),
                "market": detect_market(code),
                "security_type": it.get("SecurityTypeName"),
            }
    except Exception:
        pass
    m, secid = secid_of(code)
    return {"secid": secid, "name": None, "em_code": None, "market": m}


# --------------------------------------------------------------------------- #
# envelope
# --------------------------------------------------------------------------- #
def envelope(endpoint, code, resolved, status, data, source="L1:eastmoney",
             note=None, started=None):
    return {
        "endpoint": endpoint,
        "code": code,
        "resolved": {k: v for k, v in resolved.items() if v is not None},
        "status": status,
        "source": source,
        "as_of": datetime.now(CN_TZ).isoformat(timespec="seconds"),
        "data": data,
        "note": note,
        "latency_ms": int((time.time() - started) * 1000) if started else None,
    }


def unavailable(endpoint, code, why):
    return envelope(endpoint, code, {"market": detect_market(code)},
                    "unavailable", None, note=why)


# --------------------------------------------------------------------------- #
# L1 endpoints
# --------------------------------------------------------------------------- #
def _first_ok(handlers, code, resolved, **kw):
    """Run handlers until one answers; return (data, fn). Never fakes a result."""
    errors = []
    for fn in handlers:
        try:
            return fn(code, resolved, **kw), fn
        except DataUnavailable as exc:
            errors.append(str(exc))
        except Exception as exc:
            errors.append(f"{fn.__name__}: {type(exc).__name__}: {exc}")
    raise DataUnavailable(" | ".join(errors[-2:] or ["no handler"]))


def _kline(code, resolved, days: int = 250, **kw):
    """K-line with redundancy: tencent -> eastmoney -> sina."""
    data, _ = _first_ok([tx_kline, em_kline_em, sina_kline], code, resolved,
                        days=days)
    return data


def em_quote(code: str, resolved: dict, **kw):
    data, fn = _first_ok([em_quote_em, tx_quote], code, resolved)
    return data


def em_index(code: str = "", resolved: dict | None = None, **kw):
    resolved = resolved or {"market": "cn"}
    data, fn = _first_ok([tx_index, em_index_em], code, resolved)
    return data


def _rows(payload) -> list:
    """Safely pull `data.diff` row list; the board endpoints vary in shape."""
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = data.get("diff") if isinstance(data, dict) else None
    if isinstance(rows, dict):
        rows = list(rows.values())
    return [r for r in (rows or []) if isinstance(r, dict)]


def em_search(code: str, resolved: dict, **kw):
    try:
        payload = _http(
            "https://searchapi.eastmoney.com/api/suggest/get",
            {"input": code, "type": "14", "token": EM_SEARCH_TOKEN, "count": "10"},
            referer="https://www.eastmoney.com/",
        )
        items = (payload.get("QuotationCodeTable") or {}).get("Data") or []
    except Exception as exc:
        raise DataUnavailable(f"search failed: {exc}")
    out = []
    for it in items[:10]:
        out.append({
            "code": it.get("Code"),
            "name": it.get("Name"),
            "secid": f"{it.get('MktNum')}.{it.get('Code')}",
            "market_label": it.get("MktNumTxt") or it.get("SecurityTypeName"),
            "type": it.get("SecurityTypeName"),
        })
    if not out:
        raise DataUnavailable("no match returned by search")
    return out


def em_quote_em(code: str, resolved: dict, **kw):
    secid = resolved.get("secid") or secid_of(code)[1]
    fields = ("f43,f44,f45,f46,f47,f48,f50,f51,f52,f57,f58,f60,f107,f116,f117,"
              "f162,f167,f168,f169,f170,f171,f173,f177,f85,f86,f92,f127,f128")
    try:
        payload = _http(
            "https://push2.eastmoney.com/api/qt/stock/get",
            {"secid": secid, "fields": fields, "invt": "2", "fltt": "2"},
            referer="https://quote.eastmoney.com/",
        )
        d = payload.get("data") or {}
    except Exception as exc:
        raise DataUnavailable(f"quote failed: {exc}")
    if not d.get("f58"):
        raise DataUnavailable(f"no quote payload for {secid}")
    return {
        "name": d.get("f58"),
        "price": d.get("f43"),
        "change": d.get("f169"),
        "change_pct": d.get("f170"),
        "open": d.get("f46"),
        "high": d.get("f44"),
        "low": d.get("f45"),
        "prev_close": d.get("f60"),
        "volume": d.get("f47"),
        "amount": d.get("f48"),
        "turnover_rate": d.get("f168"),
        "total_mv": d.get("f116"),
        "float_mv": d.get("f117"),
        "pe_ttm": d.get("f162"),
        "pb": d.get("f167"),
        "roe": d.get("f173"),
        "52w_high": d.get("f51"),
        "52w_low": d.get("f52"),
        "volume_ratio": d.get("f50"),
        "update_ts": d.get("f86"),
    }


def em_kline_em(code: str, resolved: dict, days: int = 250, klt: int = 101, **kw):
    secid = resolved.get("secid") or secid_of(code)[1]
    end = datetime.now(CN_TZ).strftime("%Y%m%d")
    beg = (datetime.now(CN_TZ) - timedelta(days=int(days * 1.7) + 30)).strftime("%Y%m%d")
    try:
        payload = _http(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            {
                "secid": secid, "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": str(klt), "fqt": "1", "beg": beg, "end": end, "lmt": str(days),
            },
            referer="https://quote.eastmoney.com/",
        )
        d = payload.get("data") or {}
        rows = d.get("klines") or []
    except Exception as exc:
        raise DataUnavailable(f"kline failed: {exc}")
    if not rows:
        raise DataUnavailable(f"empty kline for {secid}")
    out = []
    for line in rows:
        p = line.split(",")
        out.append({
            "date": p[0], "open": float(p[1]), "close": float(p[2]),
            "high": float(p[3]), "low": float(p[4]), "volume": float(p[5]),
            "amount": float(p[6]), "amplitude": float(p[7]) if p[7] else None,
            "chg_pct": float(p[8]) if p[8] else None,
            "chg": float(p[9]) if p[9] else None,
            "turnover": float(p[10]) if len(p) > 10 and p[10] else None,
        })
    return {"name": d.get("name"), "count": len(out), "bars": out}


def em_minute(code: str, resolved: dict, days: int = 5, **kw):
    """Recent intraday snapshots via short-window kline (best effort)."""
    try:
        data = _kline(code, resolved, days=max(int(days), 5))
    except DataUnavailable as exc:
        raise DataUnavailable(f"minute failed: {exc}")
    bars = data.get("bars") or []
    tail = bars[-int(days * 48):] if bars else []
    return {"name": data.get("name"), "granularity": "5m", "count": len(tail), "bars": tail}


def _sma(vals, n):
    if len(vals) < n:
        return None
    return round(sum(vals[-n:]) / n, 4)


def _rsi(closes, n=14):
    if len(closes) <= n:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
    ag = sum(gains[:n]) / n
    al = sum(losses[:n]) / n
    for i in range(n, len(gains)):
        ag = (ag * (n - 1) + gains[i]) / n
        al = (al * (n - 1) + losses[i]) / n
    if al == 0:
        return 100.0
    rs = ag / al
    return round(100 - 100 / (1 + rs), 2)


def _ema(vals, n):
    if not vals:
        return []
    k = 2 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def technical_from_bars(bars: list) -> dict:
    closes = [b["close"] for b in bars]
    if len(closes) < 30:
        return {"error": "need >=30 bars"}
    ma5, ma10, ma20, ma60 = (_sma(closes, n) for n in (5, 10, 20, 60))
    dif_line = [a - b for a, b in zip(_ema(closes, 12), _ema(closes, 26))]
    dea = _ema(dif_line, 9)
    macd_hist = round((dif_line[-1] - dea[-1]) * 2, 4)
    std20 = (sum((c - (ma20 or 0)) ** 2 for c in closes[-20:]) / 20) ** 0.5
    k, d = 50.0, 50.0
    for i in range(13, len(bars)):
        win = bars[i - 8:i + 1]
        hi, lo = max(b["high"] for b in win), min(b["low"] for b in win)
        rsv = (bars[i]["close"] - lo) / (hi - lo) * 100 if hi != lo else 50
        k = 2 / 3 * k + 1 / 3 * rsv
        d = 2 / 3 * d + 1 / 3 * k
    return {
        "ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60,
        "rsi14": _rsi(closes),
        "macd": {"dif": round(dif_line[-1], 4), "dea": round(dea[-1], 4), "hist": macd_hist},
        "boll": {
            "mid": ma20,
            "upper": round(ma20 + 2 * std20, 4) if ma20 else None,
            "lower": round(ma20 - 2 * std20, 4) if ma20 else None,
        },
        "kdj": {"k": round(k, 2), "d": round(d, 2), "j": round(3 * k - 2 * d, 2)},
        "bars_used": len(closes),
    }


def em_technical(code: str, resolved: dict, days: int = 250, **kw):
    data = _kline(code, resolved, days=max(days, 120))
    tech = technical_from_bars(data.get("bars") or [])
    if "error" in tech:
        raise DataUnavailable(tech["error"])
    tech["name"] = data.get("name")
    return tech


def em_fund_flow(code: str, resolved: dict, days: int = 20, **kw):
    secid = resolved.get("secid") or secid_of(code)[1]
    try:
        payload = _http(
            "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get",
            {
                "lmt": str(days), "klt": "101", "secid": secid,
                "fields1": "f1,f2,f3,f7",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
            },
            referer="https://data.eastmoney.com/",
        )
        rows = (payload.get("data") or {}).get("klines") or []
    except Exception as exc:
        raise DataUnavailable(f"fund_flow failed: {exc}")
    if not rows:
        raise DataUnavailable("empty fund flow")
    out = []
    for line in rows:
        p = line.split(",")
        out.append({
            "date": p[0], "main_net": float(p[1]), "small_net": float(p[2]),
            "mid_net": float(p[3]), "big_net": float(p[4]), "huge_net": float(p[5]),
            "main_net_pct": float(p[6]) if p[6] else None,
        })
    latest = out[-1]
    recent5 = sum(x["main_net"] for x in out[-5:])
    return {
        "latest": latest,
        "main_net_5d": round(recent5, 2),
        "main_net_trend": "inflow" if recent5 > 0 else "outflow",
        "history": out,
    }


def em_finance(code: str, resolved: dict, periods: int = 8, **kw):
    """Key financial indicators from the F10 datacenter (A-share focused)."""
    em_code = resolved.get("em_code") or (resolved.get("secid") or "").split(".")[-1]
    mkt = detect_market(code)
    suffix = {"cn": "SH", "hk": "HK", "us": "US"}[mkt]
    if resolved.get("secid", "").startswith("0."):
        suffix = "SZ"
    secucode = f"{em_code}.{suffix}"
    # NOTE: columns=ALL on purpose. Requesting a hand-picked column list makes
    # the F10 endpoint answer HTTP 400 the moment one column name is wrong, and
    # it silently broke an earlier build. Ask for everything, pick locally.
    try:
        payload = _http(
            "https://datacenter.eastmoney.com/securities/api/data/v1/get",
            {
                "reportName": "RPT_F10_FINANCE_MAINFINADATA",
                "columns": "ALL",
                "filter": f'(SECUCODE="{secucode}")',
                "source": "HSF10", "client": "PC",
                "sortColumns": "REPORT_DATE", "sortTypes": "-1",
                "pageSize": str(periods),
            },
            referer="https://emweb.securities.eastmoney.com/",
        )
        rows = (payload.get("result") or {}).get("data") or []
    except Exception as exc:
        raise DataUnavailable(f"finance failed: {exc}")
    if not rows:
        raise DataUnavailable(f"no financial record for {secucode}")

    def pick(r, *names):
        for n in names:
            if r.get(n) is not None:
                return r.get(n)
        return None

    return {
        "secucode": secucode,
        "statements": [
            {
                "report_date": (pick(r, "REPORT_DATE") or "")[:10] or None,
                "eps": pick(r, "EPSJB", "EPSKCJB"),
                "bps": pick(r, "BPS"),
                "operating_income": pick(r, "TOTAL_OPERATE_INCOME"),
                "net_profit": pick(r, "PARENT_NETPROFIT"),
                "income_yoy": pick(r, "YSTZ", "TOTAL_OPERATE_INCOME_SQYO"),
                "profit_yoy": pick(r, "SJLTZ", "PARENT_NETPROFIT_SQYO"),
                "roe": pick(r, "ROEJQ", "WEIGHTAVG_ROE"),
                "gross_margin": pick(r, "XSMLL"),
                "net_margin": pick(r, "XSJLL"),
                "debt_ratio": pick(r, "ZCFZL"),
                "operating_cash_flow_ps": pick(r, "MGJYXJJE"),
            }
            for r in rows
        ],
    }


def em_profile(code: str, resolved: dict, **kw):
    em_code = resolved.get("em_code") or (resolved.get("secid") or "").split(".")[-1]
    suffix = {"cn": "SH", "hk": "HK", "us": "US"}[detect_market(code)]
    if resolved.get("secid", "").startswith("0."):
        suffix = "SZ"
    try:
        payload = _http(
            "https://datacenter.eastmoney.com/securities/api/data/v1/get",
            {
                "reportName": "RPT_F10_BASIC_ORGINFO",
                "columns": "SECURITY_CODE,SECURITY_NAME_ABBR,ORG_NAME,EM2016,"
                           "INDUSTRYCSRC1,BUSINESS_SCOPE,PROVINCE,ADDRESS,"
                           "FOUND_DATE,LISTING_DATE,EMP_NUM,MAIN_BUSINESS",
                "filter": f'(SECUCODE="{em_code}.{suffix}")',
                "source": "HSF10", "client": "PC", "pageSize": "1",
            },
            referer="https://emweb.securities.eastmoney.com/",
        )
        rows = (payload.get("result") or {}).get("data") or []
    except Exception as exc:
        raise DataUnavailable(f"profile failed: {exc}")
    if not rows:
        raise DataUnavailable("no company profile")
    r = rows[0]
    return {
        "code": r.get("SECURITY_CODE"), "name": r.get("SECURITY_NAME_ABBR"),
        "org_name": r.get("ORG_NAME"), "industry_csrc": r.get("INDUSTRYCSRC1"),
        "province": r.get("PROVINCE"), "address": r.get("ADDRESS"),
        "found_date": r.get("FOUND_DATE"), "listing_date": r.get("LISTING_DATE"),
        "employees": r.get("EMP_NUM"),
        "main_business": (r.get("MAIN_BUSINESS") or r.get("EM2016") or "")[:600],
    }


def em_dividend(code: str, resolved: dict, periods: int = 8, **kw):
    """Dividend history.

    The public F10 endpoint exposes no reliable dividend report, so L1 gives up
    honestly and we fall through to AKShare (L2). DDM valuation depends on this,
    so callers MUST check `status` before using it.
    """
    ak = _try_import("akshare")
    if not ak:
        raise DataUnavailable(
            "L1 has no dividend endpoint; install AKShare for L2 "
            "(pip install akshare) -> stock_fhps_detail_em(symbol='600519')"
        )
    em_code = resolved.get("em_code") or (resolved.get("secid") or "").split(".")[-1]
    symbol = None
    try:
        df = ak.stock_fhps_detail_em(date="")           # full market history
        symbol = em_code
        rows = df[df["股票代码"].astype(str) == str(symbol)].tail(int(periods))
        out = [
            {
                "report_date": str(r.get("报告期", ""))[:10],
                "plan": r.get("分红方案"),
                "cash_per_share": r.get("现金分红-现金分红比例"),
                "dividend_yield": r.get("现金分红-股息率"),
                "ex_date": r.get("除权除息日"),
            }
            for _, r in rows.iterrows()
        ]
        if out:
            return {"symbol": symbol, "history": out}
    except Exception as exc:
        raise DataUnavailable(f"akshare dividend failed: {exc}")
    raise DataUnavailable("no dividend record available")


def em_shareholder(code: str, resolved: dict, top: int = 10, **kw):
    em_code = resolved.get("em_code") or (resolved.get("secid") or "").split(".")[-1]
    suffix = {"cn": "SH", "hk": "HK", "us": "US"}[detect_market(code)]
    if resolved.get("secid", "").startswith("0."):
        suffix = "SZ"
    payload_rows = []
    try:
        payload = _http(
            "https://datacenter.eastmoney.com/securities/api/data/v1/get",
            {
                "reportName": "RPT_F10_EH_FREEHOLDERS",
                "columns": "ALL",
                "filter": f'(SECUCODE="{em_code}.{suffix}")',
                "source": "HSF10", "client": "PC",
                "sortColumns": "HOLDER_RANK", "sortTypes": "1",
                "pageSize": str(top),
            },
            referer="https://emweb.securities.eastmoney.com/",
        )
        payload_rows = (payload.get("result") or {}).get("data") or []
    except Exception:
        payload_rows = []
    holders = [
        {
            "rank": r.get("HOLDER_RANK"), "name": r.get("HOLDER_NAME"),
            "hold_num": r.get("HOLD_NUM"), "ratio": r.get("FREE_HOLDNUM_RATIO"),
            "type": r.get("HOLDER_TYPE"), "change": r.get("HOLD_NUM_CHANGE"),
        }
        for r in payload_rows[:top]
    ]
    if not holders:
        raise DataUnavailable("no shareholder detail (non A-share or not disclosed)")
    latest = payload_rows[0].get("END_DATE")
    return {"end_date": (latest or "")[:10] or latest, "top10_free": holders}


def em_notice(code: str, resolved: dict, size: int = 10, **kw):
    """Exchange announcements.

    L1 could not reliably reach the public notice endpoint, so this is an L2-only
    capability (AKShare -> cninfo disclosure report). We prefer returning
    `unavailable` over inventing announcement rows.
    """
    ak = _try_import("akshare")
    if not ak:
        raise DataUnavailable(
            "L1 has no reliable announcement endpoint; install AKShare for L2 "
            "(pip install akshare) -> stock_zh_a_disclosure_report_cninfo"
        )
    em_code = resolved.get("em_code") or (resolved.get("secid") or "").split(".")[-1]
    try:
        df = ak.stock_zh_a_disclosure_report_cninfo(symbol=str(em_code))
        rows = df.head(int(size))
    except Exception as exc:
        raise DataUnavailable(f"akshare disclosure failed: {exc}")
    return {
        "items": [
            {
                "title": r.get("公告标题"), "date": str(r.get("公告时间", ""))[:10],
                "type": r.get("公告类型"), "url": r.get("公告链接"),
            }
            for _, r in rows.iterrows()
        ]
    }


def em_news(code: str, resolved: dict, size: int = 15, **kw):
    name = resolved.get("name") or code
    param = {
        "uid": "", "keyword": name, "type": ["cmsArticleWebOld"],
        "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {
            "searchScope": "default", "sort": "time", "pageIndex": 1,
            "pageSize": size, "preTag": "<em>", "postTag": "</em>"}},
    }
    try:
        payload = _http(
            "https://search-api-web.eastmoney.com/search/jsonp",
            {"cb": "callback", "param": json.dumps(param, ensure_ascii=False)},
            referer="https://so.eastmoney.com/",
        )
        node = (payload.get("result") or {}).get("cmsArticleWebOld")
        # search-api returns either a plain LIST of articles or an object with
        # {"list": [...]} depending on the endpoint version - accept both.
        items = node if isinstance(node, list) else ((node or {}).get("list") or [])
    except Exception as exc:
        raise DataUnavailable(f"news failed: {exc}")
    if not isinstance(items, list) or not items:
        raise DataUnavailable("no news items")
    return {
        "items": [
            {
                "title": (it.get("title") or "").replace("<em>", "").replace("</em>", ""),
                "date": it.get("date") or it.get("datetime"),
                "media": it.get("mediaName"),
                "url": it.get("url"),
                "summary": ((it.get("content") or "").replace("<em>", "")
                            .replace("</em>", ""))[:200],
            }
            for it in items
        ]
    }


def em_hot(code: str, resolved: dict, size: int = 20, **kw):
    """Hot / most-watched ranking board."""
    try:
        payload = _http(
            "https://push2.eastmoney.com/api/qt/clist/get",
            {"pn": "1", "pz": str(size), "po": "1", "fid": "f6",
             "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
             "fields": "f12,f14,f2,f3,f6,f62"},
            referer="https://data.eastmoney.com/",
        )
        rows = _rows(payload)
    except Exception as exc:
        raise DataUnavailable(f"hot failed: {exc}")
    if not rows:
        raise DataUnavailable("empty hot board")
    return {"board": "热门资金榜", "items": [
        {"code": r.get("f12"), "name": r.get("f14"), "price": r.get("f2"),
         "chg_pct": r.get("f3"), "main_net": r.get("f62")} for r in rows]}


def em_index_em(code: str = "", resolved: dict | None = None, size: int = 6, **kw):
    """Major index snapshot (used by macro / market-overview steps)."""
    targets = ["1.000001", "0.399001", "0.399006", "1.000688", "0.399905", "1.000300"]
    fields = "f12,f14,f2,f3,f4,f6"
    try:
        payload = _http(
            "https://push2.eastmoney.com/api/qt/ulist.np/get",
            {"fltt": "2", "secids": ",".join(targets), "fields": fields},
            referer="https://quote.eastmoney.com/",
        )
        rows = _rows(payload)
    except Exception as exc:
        raise DataUnavailable(f"index failed: {exc}")
    if not rows:
        raise DataUnavailable("empty index board")
    return {"as_of": datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "items": [{"code": r.get("f12"), "name": r.get("f14"),
                       "price": r.get("f2"), "chg_pct": r.get("f3"),
                       "chg": r.get("f4"), "amount": r.get("f6")} for r in rows]}


def em_sector(code: str, resolved: dict, size: int = 20, **kw):
    """Industry board ranking - supplies the industry-chain positioning step."""
    try:
        payload = _http(
            "https://push2.eastmoney.com/api/qt/clist/get",
            {"pn": "1", "pz": str(size), "po": "1", "np": "1", "fltt": "2",
             "invt": "2", "fid": "f3", "fs": "m:90+t:2+f:!50",
             "fields": "f12,f14,f3,f104,f105,f128,f136"},
            referer="https://quote.eastmoney.com/",
        )
        rows = _rows(payload)
    except Exception as exc:
        raise DataUnavailable(f"sector failed: {exc}")
    if not rows:
        raise DataUnavailable("empty sector board")
    return {"items": [
        {"board_code": r.get("f12"), "board_name": r.get("f14"),
         "chg_pct": r.get("f3"), "up_count": r.get("f104"),
         "down_count": r.get("f105"), "leader": r.get("f128"),
         "leader_chg": r.get("f136")} for r in rows]}


# --------------------------------------------------------------------------- #
# optional channels (L2 akshare / L3 yfinance)
# --------------------------------------------------------------------------- #
def _try_import(mod: str):
    try:
        return __import__(mod)
    except Exception:
        return None


def yf_for(code: str) -> str | None:
    """hk00700 -> 0700.HK ; usAAPL -> AAPL ; returns None for A-share."""
    m = detect_market(code)
    c = (code or "").strip().lower()
    if m == "hk":
        body = c[2:] if c.startswith("hk") else c
        return body.zfill(4) + ".HK"
    if m == "us":
        return (c[2:] if c.startswith("us") else c).upper()
    return None


def l3_us_quote(code: str, resolved: dict, **kw):
    yf = _try_import("yfinance")
    if not yf:
        raise DataUnavailable("yfinance not installed (pip install yfinance)")
    ticker = yf_for(code)
    if not ticker:
        raise DataUnavailable("not applicable")
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.fast_info or {}
    except Exception:
        pass
    hist = None
    try:
        hist = t.history(period="6mo")
    except Exception:
        pass
    last = None
    if hist is not None and len(hist):
        last = float(hist["Close"].iloc[-1])
    return {
        "name": info.get("long_name") or ticker,
        "price": last or info.get("last_price"),
        "prev_close": info.get("previous_close"),
        "total_mv": info.get("market_cap"),
        "pe_ttm": info.get("trailing_pe"),
        "pb": info.get("price_to_book"),
        "52w_high": info.get("year_high"),
        "52w_low": info.get("year_low"),
        "source_detail": "yfinance fast_info/history",
    }


def l2_ak_north(code: str, resolved: dict, days: int = 30, **kw):
    ak = _try_import("akshare")
    if not ak:
        raise DataUnavailable("akshare not installed (pip install akshare)")
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
    except Exception as exc:
        raise DataUnavailable(f"akshare failed: {exc}")
    tail = df.tail(10)
    return {"latest": tail.to_dict(orient="records")[-1] if len(tail) else None,
            "rows": tail.to_dict(orient="records")}


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #
def _l2_only(akshare_fn: str):
    """Declare an endpoint that only exists on the AKShare channel.

    We deliberately return `unavailable` instead of substituting look-alike data:
    a wrong number that looks plausible is worse than an admitted gap. Every
    consumer in this repo is required to print `status` when it is not `ok`.
    """
    def _fn(code, resolved, **kw):
        raise DataUnavailable(
            f"this endpoint needs L2 akshare -> pip install akshare, "
            f"then {akshare_fn}"
        )
    return _fn


ENDPOINTS: dict[str, tuple[list, bool]] = {
    # endpoint       handler redundancy chain            needs symbol?
    "search":        ([em_search],                        False),
    "quote":         ([l3_us_quote, em_quote, tx_quote],  True),
    "kline":         ([tx_kline, em_kline_em, sina_kline], True),
    "minute":        ([em_minute],                        True),
    "technical":     ([em_technical],                     True),
    "fund_flow":     ([em_fund_flow],                     True),
    "finance":       ([em_finance],                       True),
    "profile":       ([em_profile],                       True),
    "dividend":      ([em_dividend],                      True),
    "shareholder":   ([em_shareholder],                   True),
    "news":          ([em_news],                          True),
    "notice":        ([em_notice],                        True),
    "hot":           ([em_hot],                           False),
    "index":         ([tx_index, em_index_em],            False),
    "sector":        ([em_sector],                        False),
    "north_holding": ([l2_ak_north],                      False),
    "us_quote":      ([l3_us_quote],                      True),
    # honest L2-only endpoints (no silent substitution)
    "lhb":           ([_l2_only("akshare.stock_lhb_detail_em(start_date=..., end_date=...)")], True),
    "margin":        ([_l2_only("akshare.stock_margin_detail_sse / stock_margin_detail_szse")], True),
    "consensus":     ([_l2_only("akshare.stock_zh_valuation_baidu(symbol=..., indicator='PE')")], True),
    "chip":          ([_l2_only("akshare.stock_cyq_em(symbol=...) chip distribution")], True),
    "score":         ([em_technical],                     True),   # transparent composite
}

ENDPOINT_NOTES = {
    "score": "诊股评分 replaced by a transparent technical composite "
             "(MA/RSI/MACD/BOLL/KDJ) - we publish the formula instead of a black box.",
}

# --------------------------------------------------------------------------- #
# aliases
# --------------------------------------------------------------------------- #
# The nine employees used to speak proprietary connector verbs (data_risk,
# data_report, ...). Rather than rewriting every workflow, we map those verbs to
# the closest honest public endpoint and tag them with a note, so a report can
# say "DERIVED FROM NEWS" instead of pretending to have privileged data.
ALIASES: dict[str, tuple[str, str]] = {
    "industry_chain": ("sector", "industry board ranking used as a proxy for 产业链图谱"),
    "market_overview": ("index", "index board used as a proxy for 大盘总览"),
    "south_holding": ("north_holding", "southbound capital - same HSGT family (L2)"),
    "report": ("news", "research reports approximated by news headlines - LABEL IT"),
    "dehydrated": ("news", "dehydrated research approximated by news - LABEL IT"),
    "disclosure": ("notice", "disclosure schedule approximated by announcements"),
    "suspension": ("notice", "trading halt status via announcements"),
    "events": ("news", "event tags approximated by news feed - LABEL IT"),
    "risk": ("news", "risk events approximated by news feed - LABEL IT"),
    "calendar": ("notice", "disclosure calendar via announcements"),
    "rating": ("news", "broker ratings approximated by news feed - LABEL IT"),
    "notice_list": ("notice", "alias of notice"),
}

# Remaining L2/L3-only endpoints document their gap inside `note` at call time.

DESCRIPTIONS = {
    "search": "fuzzy symbol search / 模糊搜索代码",
    "quote": "realtime quote snapshot / 实时行情快照",
    "kline": "daily OHLCV history / 日 K 线",
    "minute": "recent 5-minute bars / 近 5 日分时",
    "technical": "MA/RSI/MACD/BOLL/KDJ computed from kline / 技术指标",
    "fund_flow": "money flow (main/mid/small) / 资金流向",
    "finance": "key financial indicators / 主要财务指标",
    "profile": "company profile / 公司概况",
    "dividend": "dividend history / 分红历史",
    "shareholder": "top circulating holders / 十大流通股东",
    "news": "recent news / 最新新闻",
    "notice": "exchange announcements / 交易所公告",
    "hot": "hot money ranking board / 资金热度榜",
    "index": "major index snapshot / 大盘指数",
    "sector": "industry board ranking / 行业板块排行",
    "north_holding": "northbound capital via AKShare / 北向资金(L2)",
    "us_quote": "HK/US quote via yfinance / 港美股行情(L3)",
    "lhb": "dragon-tiger list (L2 only) / 龙虎榜(需 L2)",
    "margin": "margin trading detail (L2 only) / 融资融券(需 L2)",
    "consensus": "broker consensus (L2 only) / 机构一致预期(需 L2)",
    "chip": "chip distribution (L2 only) / 筹码分布(需 L2)",
    "score": "transparent composite score / 诊股综合评分(透明)",
}

for _alias, (_target, _reason) in ALIASES.items():
    ENDPOINTS.setdefault(_alias, ENDPOINTS[_target])
    ENDPOINT_NOTES.setdefault(_alias, _reason)
    DESCRIPTIONS.setdefault(_alias, DESCRIPTIONS.get(_target, ""))


def call(endpoint: str, code: str, **kw) -> dict:
    started = time.time()
    endpoint = endpoint.strip()
    if endpoint not in ENDPOINTS:
        return {
            "endpoint": endpoint, "code": code, "status": "unavailable",
            "source": None, "as_of": datetime.now(CN_TZ).isoformat(timespec="seconds"),
            "data": None, "latency_ms": 0,
            "note": f"unknown endpoint {endpoint!r}; run `python fin_data.py list`",
        }
    handlers, _needs_symbol = ENDPOINTS[endpoint]
    resolved = {"market": detect_market(code)}
    try:
        if endpoint not in ("search", "index", "hot", "sector", "north_holding"):
            resolved.update(resolve(code))
    except Exception:
        pass
    # yfinance (L3) only makes sense for HK/US symbols
    if endpoint == "quote" and detect_market(code) == "cn":
        handlers = [h for h in handlers if not h.__name__.startswith("l3_")]
    last_err = None
    for fn in handlers:
        try:
            data = fn(code, resolved, **kw)
            note = ENDPOINT_NOTES.get(endpoint)
            status = "degraded" if note else "ok"
            return envelope(endpoint, code, resolved, status, data,
                            source=_source_of(fn), note=note, started=started)
        except DataUnavailable as exc:
            last_err = str(exc)
        except Exception as exc:                      # never crash the pipeline
            last_err = f"{type(exc).__name__}: {exc}"
    return envelope(endpoint, code, resolved, "unavailable", None,
                    note=last_err, started=started)


def _source_of(fn) -> str:
    name = getattr(fn, "__name__", "")
    for prefix, label in (("l2_", "L2:akshare"), ("l3_", "L3:yfinance"),
                          ("tx_", "L1:tencent"), ("sina_", "L1:sina")):
        if name.startswith(prefix):
            return label
    return "L1:eastmoney"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="fin_data.py",
        description="Unified financial data layer for the FinAI Digital Workforce",
    )
    ap.add_argument("endpoint", nargs="?", default="list")
    ap.add_argument("code", nargs="?", default=None)
    ap.add_argument("--days", type=int, default=250)
    ap.add_argument("--size", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="machine readable output")
    args = ap.parse_args(argv)

    if args.endpoint in ("list", "help"):
        print("Endpoints of fin_data.py (unified financial data layer)\n")
        for k, (_, need_symbol) in ENDPOINTS.items():
            print(f"  {k:<15} {'<code>' if need_symbol else '':<7} {DESCRIPTIONS.get(k,'')}")
        print("\nExample: python fin_data.py quote sh600519 --json")
        return 0

    if ENDPOINTS.get(args.endpoint, (None, True))[1] and not args.code:
        print(f"error: endpoint '{args.endpoint}' needs a code", file=sys.stderr)
        return 2

    kw = {"days": args.days}
    if args.endpoint in ("news", "notice", "hot", "sector"):
        kw["size"] = args.size
    result = call(args.endpoint, args.code or "", **kw)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
