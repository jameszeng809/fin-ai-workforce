# 🌐 shared/ · 统一金融数据层 Unified Data Layer

> All nine employees read market data through **one** file: `fin_data.py`.
> 九个数字员工共用同一份数据入口。

| 特性 Feature | 说明 Description |
|---|---|
| 🔑 **零 API Key** | 无需注册任何平台、无需任何密钥 No signup, no keys, no quota |
| 📦 **零必需依赖** | 核心功能仅用 Python 标准库 Core works with stdlib only |
| 🛡️ **诚实降级** | 每个响应带 `status`：`ok` / `degraded` / `unavailable`，从不静默造假 Every response carries `status`; nothing is silently faked |
| 🌍 **跨市场** | A股 / 港股 / 美股统一入口 One interface for CN / HK / US |

## 用法 Usage

```bash
python shared/fin_data.py list                       # 列出全部端点 list all endpoints
python shared/fin_data.py quote sh600519             # 实时行情 realtime quote
python shared/fin_data.py kline sh600519 --days 250  # 日K日线 bars
python shared/fin_data.py technical hk00700          # 技术指标 indicators
python shared/fin_data.py finance usAAPL             # 财务指标 financials
```

作为 Python 模块调用 / As a library:

```python
import sys; sys.path.insert(0, "shared")
import fin_data

r = fin_data.call("quote", "sh600519")
print(r["status"], r["source"], r["data"]["price"])
```

统一响应信封 Unified envelope:

```json
{
  "endpoint": "quote",
  "code": "sh600519",
  "resolved": {"secid": "1.600519", "name": "贵州茅台", "market": "cn"},
  "status": "ok",
  "source": "L1:eastmoney",
  "as_of": "2026-10-25T16:19:28+08:00",
  "data": { "price": 1335.0, "pe_ttm": 18.74, "pb": 6.64 },
  "note": null,
  "latency_ms": 1506
}
```

## ⚠️ 单位陷阱（务必读完）Unit traps you must read

| 字段 Field | 单位 Unit | 说明 Note |
|---|---|---|
| `bar.volume` | A股「手」(100 shares) / 港美股「股」(shares) | **原始值，勿直接当股数用** |
| `bar.shares` | 股 shares | 已按市场归一化 Use this one |
| `bar.amount` | 元 CNY / HKD / USD | 由 `shares × close` 推导 Derived, not billed data |
| `quote.float_mv` / `total_mv` | 亿 (100 million) | 见响应中的 `unit_note` |
| `finance.statements[*]` | 元 CNY / USD | **看 `data.currency`，港股常为人民币** |

> 曾经的真实事故：把「手」当「股」计算 20 日日均成交额（ADV），结果缩小 100 倍，
> 导致交易执行官把**每一笔**订单都判成"超过单日成交额、禁止执行"。
> A real incident: reading lots as shares understated ADV by 100x, so the
> execution employee refused every single order.

### 💱 币种陷阱 Currency trap

港股公司**以 HKD 报价、却以人民币披露财报**。若直接拿人民币的每股价值去比 HKD 现价，
结果会系统性低估约 15%，而且**不会报任何错**——这是本项目最忌讳的静默错误。

Hong Kong issuers are **priced in HKD but file statements in RMB**. Dividing an RMB
per-share value by an HKD price is silently ~15% wrong. Always check
`data.currency` against the quote currency and convert with the `fx` endpoint.

```bash
python shared/fin_data.py fx --base CNY --quote HKD
# {"rate": 1.173631, "as_of": "Tue, 27 Oct 2026 00:02:31", ...}

# 自检：USD/HKD 应落在港元联系汇率区间 7.75–7.85
python shared/fin_data.py fx --base HKD --quote USD     # 0.127471 → 1/0.127471 = 7.845 ✅
```

## 跨市场覆盖 Market coverage

| 端点 Endpoint | A股 CN | 港股 HK | 美股 US |
|---|---|---|---|
| `quote` 实时行情 | ✅ | ✅ | ✅ |
| `kline` 日K（含复权） | ✅ | ✅ | ✅ 腾讯 + Nasdaq 双源 |
| `finance` 财报 | ✅ 东财 F10 宽表 | ✅ 东财 HKF10 利润表（长表转置） | ✅ Nasdaq 利润表 |
| `fx` 汇率 | ✅ CNY/HKD/USD 互换 | ✅ | ✅ |
| `news` / `index` / `search` | ✅ | ✅ | ✅ |

**三市场全覆盖。** 港股财报走 `RPT_HKF10_FN_INCOME`，返回长表（一科目一行），
本层已按报告期转置并优先取年报（`DATE_TYPE_CODE=001`）；币种随响应给出。
HK statements arrive as a long table (one row per line item); this layer pivots it
per report date and prefers annual reports.

取不到的组合一律返回 `status: "unavailable"` 并带 `note` 说明，**不会用邻近市场的数据顶替**。
Misses return `unavailable` with a reason — never substituted with another market's data.

## 三级通道 Three tiers

| Tier | 覆盖 Coverage | 依赖 Requirement |
|---|---|---|
| **L1 公开数据源** | 行情 / K线 / 技术指标 / 财务 / 股东 / 新闻 / 指数 / 板块 | 无 none |
| **L2 AKShare** | 龙虎榜 / 融资融券 / 筹码分布 / 分红 / 北向资金 | `pip install akshare` |
| **L3 yfinance** | 港美股深度数据 | `pip install yfinance` |

## 端点清单 Endpoints

| 端点 Endpoint | 符号 Symbol? | 说明 Description | 通道 Tier |
|---|:--:|---|---|
| `search` | ❌ | 模糊代码搜索 fuzzy symbol search | L1 |
| `quote` | ✅ | 实时行情 realtime quote | L1 → L3 |
| `kline` | ✅ | 日K线 daily bars | L1 |
| `minute` | ✅ | 近 5 日分时 recent intraday | L1 |
| `technical` | ✅ | MA/RSI/MACD/BOLL/KDJ | L1 |
| `fund_flow` | ✅ | 资金流向 money flow | L1 |
| `finance` | ✅ | 主要财务指标 key financials | L1 |
| `profile` | ✅ | 公司概况 company profile | L1 |
| `dividend` | ✅ | 分红历史 dividend history | L2 |
| `shareholder` | ✅ | 十大流通股东 top holders | L1 |
| `news` | ✅ | 最新新闻 news feed | L1 |
| `notice` | ✅ | 交易所公告 announcements | L2 |
| `hot` | ❌ | 资金热度榜 hot board | L1 |
| `index` | ❌ | 大盘指数 major indices | L1 |
| `sector` | ❌ | 行业板块排行 industry boards | L1 |
| `north_holding` | ❌ | 北向资金 northbound flows | L2 |
| `us_quote` | ✅ | 港美股行情 HK/US quote | L3 |
| `lhb` `margin` `consensus` `chip` | ✅ | 龙虎榜/融资融券/一致预期/筹码 distribution data | L2 |

另有别名兼容 formerly-proprietary verbs: `industry_chain` / `market_overview` /
`south_holding` / `report` / `dehydrated` / `disclosure` / `suspension` /
`events` / `risk` / `calendar` / `rating` → mapped to the nearest public endpoint,
each carrying a `degraded` note that **must** be surfaced in any report.

## 工程笔记 Implementation notes

三个踩过的坑写在代码注释里，避免后人重复踩：Three hard-won notes are kept in the code comments:

1. **TLS 指纹**。部分国内行情接口按 ClientHello 特征拒绝 Python 的 `urllib`，却放行 `curl`。
   因此传输层是级联的：`urllib → curl → 退避 1.2s → urllib → curl`。
   Some endpoints reject Python's TLS fingerprint while accepting curl — hence the transport cascade.
2. **不要手写列名**。`datacenter` 接口的 `columns=` 一旦有一个列名不存在就返回 HTTP 400，
   曾经导致整个财报拉取静默失效。现在统一 `columns=ALL` 后本地挑选。
   A single wrong column name yields HTTP 400 — we request `ALL` and pick locally.
3. **节制请求**。层内置 0.5s 最小间隔 + 退避重试，避免在共享 IP 上触发限流。
   Built-in 0.5s throttle and backoff keep us a polite guest on shared IPs.

## 🛡️ 数据诚实原则 Honesty contract

`status != "ok"` 时**禁止**用估算值填充，必须在产出中显式披露。
这不只是一句口号，它是本仓库所有 SKILL.md 的硬性约束。

When `status` is not `ok`, you **must** surface it — never backfill. This is a hard rule
across every `SKILL.md` in this repository.
