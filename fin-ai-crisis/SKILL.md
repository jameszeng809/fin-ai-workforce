---
name: fin-ai-crisis
slug: fin-ai-crisis
displayName: 普惠金融数字团队-应急交易员
version: "4.0.0"
description: >
  普惠金融数字员工团队的"应急交易员"角色。
  当持仓股票突发负面消息时，5 分钟内自动完成
  舆情分级 → 历史案例匹配 → 影响评估 → 减仓方案 → 模拟试单 → 一键执行，
  最终输出应急作战方案 HTML。支持公开数据源 模拟撮合（本地 paper trading） 真实模拟试单。
author: jameszeng809
agent_created: true
tags:
  - finance
  - crisis-management
  - red-alert
  - 5min-decision
  - digital-employee
  - fin-ai-team
  - open-finance-data
parent_skill: fin-ai-terminal
data_source:
  - shared/fin_data.py  # 统一金融数据层：公开数据源，零 API Key，全球可用
trigger_phrases:
  - 突发舆情
  - 应急响应
  - 黑天鹅
  - 5分钟决策
  - 减仓方案
  - crisis response
  - 5 minute decision
---
## 团队归属与运行模式

> **本项目是「普惠金融数字员工团队」的其中一员**，可独立作为数字员工「超级个体」运行，也可整个团队下载后作为整体「超级团队」运行。
>
> 如希望运行「超级团队」，请搜索 **「普惠金融数字团队-CIO 主理人」** 页面，按指引一键安装全部 9 名数字员工，由 CIO 主理人调度 3 轮圆桌会议即可获得「群体智能」决策。

### 团队成员清单（9 名数字员工）

| 中文花名 | Skill ID | 核心职能 |
|---------|---------|---------|
| 深度研究员 | fin-ai-researcher | DCF/PE/PB/DDM 估值 + 蒙特卡洛 |
| 投研经理 | fin-ai-portfolio | Brinson 归因 + 组合调仓 |
| 风控官 | fin-ai-risk | VaR + 压力测试 + 三级预警 |
| 应急交易员 | fin-ai-crisis | 舆情 5 分钟减仓 + 模拟试单 |
| 舆情监控官 | fin-ai-news | 7×24 扫描 + 自动分级 |
| 量化分析师 | fin-ai-quant | Fama-French + Black-Litterman |
| 合规专员 | fin-ai-compliance | 信披 + 关联交易识别 |
| 交易执行官 | fin-ai-execution | TWAP/VWAP/POV/Iceberg/Sniper |
| **CIO 主理人** | **fin-ai-orchestrator** | **3 轮圆桌会议 + 共识度评分** |

---

## 🌐 数据获取方式（统一数据层 · 零 API Key）

本项目**不依赖任何私有连接器**。所有行情/基本面数据来自仓库内置的统一数据层：

```bash
# 语法：python shared/fin_data.py <端点> <股票代码>
python shared/fin_data.py quote    sh600519     # 实时行情（含 PE/PB/市值/换手率）
python shared/fin_data.py kline    sh600519 --days 250
python shared/fin_data.py finance  sh600519     # 主要财务指标（8 期）
python shared/fin_data.py news     sh600519     # 最新新闻
python shared/fin_data.py list                  # 查看全部端点
```

| 数据通道 | 覆盖范围 | 需要 Key？ |
|---|---|:---:|
| **L1 公开数据源**（默认，零依赖） | 行情 / K线 / 技术指标 / 财务 / 股东 / 新闻 / 指数 / 板块 | ❌ |
| **L2 AKShare**（可选 `pip install akshare`） | A股深度：龙虎榜 / 融资融券 / 筹码分布 / 分红 / 北向资金 | ❌ |
| **L3 yfinance**（可选 `pip install yfinance`） | 港美股深度数据 | ❌ |

> **数据诚实原则（硬性）**：每次调用返回 `status` 字段 —— `ok` / `degraded` / `unavailable`。
> 凡是 `degraded` 或 `unavailable` 的字段，**必须在报告中显式披露数据来源状态**，
> **禁止**用估算值静默填充。宁可给出「该指标不可得」的专业结论，也不编造数字。

---


# 普惠金融-应急交易员 (fin-ai-crisis) v3.0

## 用途

「普惠金融数字员工团队」中的**应急交易员**角色，对标真实基金的"突发事件处置小组"。
v3.0 升级：**接入公开数据源实时舆情 + 历史案例库 + 模拟交易**，让"5 分钟决策"
从"口头建议"变成"可执行指令"。

## v3.0 升级亮点

| 维度 | v1/v2 手动触发版 | **v3.0 自动化触发 + 真实执行** |
|------|------|------|
| 舆情来源 | 人工输入 | **data_news + data_notice 自动触发** |
| 历史案例 | 无 | **康美/康得新/瑞幸 50+ 案** |
| 影响评估 | 模板估算 | **+ 资金流向 + 龙虎榜 + 卖空压力** |
| 减仓方案 | 通用建议 | **+ 模拟撮合（本地 paper trading） 试单验证** |
| 执行 | 不支持 | **一键触发模拟交易** |

## 工作流程（5 步 · 5 分钟硬约束 · 显式并行 DAG）

> **DAG 与超时降级（v3.2.0）**：Step 2/3 并行执行 → 汇合后 Step 4 → 确认闸门 → Step 5。每个节点超时 10 秒即降级（案例匹配降为"仅规则分级"、资金动向降为"仅 data_fund_flow"），降级必须在作战方案中显式披露。5 分钟预算倒排：接入分级 30s → 并行(案例+资金) 90s → 影响评估 60s → 减仓方案 60s → 闸门确认+试单 120s。

### Step 1 · **舆情自动接入 + 分级**（<10s）
- 触发方式：
  - 数据源：`fin_data.py news` + `fin_data.py notice` 监听
  - 自动化任务：每日 9:00 + 13:00 扫描
  - 主动推送：用户输入突发新闻
- 分级：
  - **P0（立即响应）**：监管处罚/立案/重大违规/退市风险
  - **P1（重要）**：业绩暴雷/重大合同/管理层变动
  - **P2（关注）**：行业利空/同行拖累

### Step 2 · **历史案例匹配**（<60s，v3.2.0 案例库落地）
**读取 `data/case_library.json`（50 条真实案例，v3.2.0 不再只凭记忆举例）**：
- 匹配规则（写在案例库文件内）：按 event_type 精确匹配 → market → severity，取相似度 Top3
- 案例库覆盖：财务造假（康美/康得新/瑞幸/紫晶存储）、债务危机（恒大/碧桂园/融创）、政策冲击（双减/反垄断）、做空报告（安踏/波司登/辉山）、产品安全（长生/三聚氰胺）、面值退市（广汇/ST爱康）等 12 类事件
- 输出：**最相似历史案例 Top3** + 同类型案例 max_drop_pct 中位数（标注样本数）+ 后续走势结局

**v3.3.0 强制脚本化（禁止 LLM 心算/凭记忆举例）**：

```bash
python scripts/match_cases.py --event-type financial_fraud --market cn --top 3
python scripts/match_cases.py --event-type debt_crisis --severity P0
python scripts/match_cases.py --event-type earnings_shock --severity P1 --market cn
python scripts/match_cases.py --list-types      # 查看 12 类事件类型与各自案例数
python scripts/match_cases.py --list-classes    # 查看杀伤等级分布（terminal/severe/moderate/minor）
```

#### ⚠️ 禁止把历史跌幅直接当预测（v3.4.1 ★ 最容易翻车的一条）

脚本输出内置 `estimation_guard`，**以下四条为硬性要求**：

1. **先看 `suggested_reference`**：按查询 severity 推荐应参考的杀伤档及其跌幅中位数
2. **再看 `impact_class_breakdown`**：同类事件按 terminal / severe / moderate / minor 分层对照，
   跨档类比（如把单季业绩小幅回落套到财务造假退市案例 -88%）必须被拦下
3. **必须做量级比较**：把本次事件的定量落差与候选案例的定量特征对比，差一个数量级则不可类比
4. **结论必须给区间 + 触发条件**，禁止输出单一跌幅数字

> 实测示例：宁德时代 2026Q3 归母净利 212.46 亿、环比 **−5.8%**、毛利率 −2.5pct。
> 若直接套用 earnings_shock 全类型中位 **−35%**，会高估约 6 倍。
> v3.4.1 已在案例中补入「苹果下调指引 −10%」「宁德 2022 毛利率下滑 −35%」「茅台增速放缓 −8%」等
> 温和/可修复样本（案例库 50 → 56 例），并让 severity 相邻衰减打分，避免 P1 事件被 P0 案例绑架。

#### 输入去重（v3.4.1）
同一事件的多源转载必须先去重再匹配，否则同一件事被算成多次：

```bash
python scripts/dedup.py --news-file news.json      # 实现 scoring.json 早有声明的 dedup 规则
```

脚本输出：Top3 相似案例（含相似度分值）+ 同类型 `max_drop_pct` 中位数/P25/P75 + **样本数** + 结局分布。
事件类型写错会直接报错并回显 12 个合法取值，杜绝凭空编造类型。

**分级依据（v3.2.0 量化，v3.3.0 脚本化）**：P0/P1/P2 由舆情监控官 scoring.json 公式输出，
必须运行 `python scripts/classify.py --sentiment <0-100> --involvement <0-100> --spread <0-100>`，
本 skill 直接采用其分级结果，不再自行分级（v3.3.0 已修正分级方向：旧公式下 P0 数学上不可达）。
> **✅ 跨 skill 依赖已内置转发壳（v3.4.0）**：`classify.py` 属于 `fin-ai-news`。若未同时安装舆情监控官，该命令会因文件不存在而失败；此时须先安装 `fin-ai-news`，或改用本 skill `data/case_library.json` 人工分级并标注「未过脚本校验」。

### Step 3 · **影响评估 + 资金动向**（<60s）
- `fin_data.py fund_flow`：当日主力资金流向
- `fin_data.py north_holding`：北向资金动向
- `fin_data.py fund_short`：卖空压力
- `fin_data.py lhb`：游资动向
- 输出：未来 5 日走势预期分布 + 资金撤离概率

### Step 4 · **减仓方案 + 替代标的**（<60s）
- 计算减仓比例（P0 推荐 50-70%，P1 推荐 20-40%，P2 推荐观察）
- 用 `fin_data.py sector` 在同行业找**估值更低 / 流动性更好**的替代
- 输出：
  - 减仓目标：股票代码 / 减仓比例 / 减仓金额
  - 加仓目标：替代股票 / 加仓比例 / 加仓金额
  - 1-7 日滚动计划

### Step 5 · **模拟试单 + 输出作战方案**（<120s）
- 调用 `模拟撮合（本地 paper trading）`：
  - 创建模拟卖出单
  - 创建模拟买入单（替代标的）
  - 看 1 日试单 PnL
- 输出：**作战方案 HTML**（含可执行的减仓 + 替代 + 试单结果）

> **⚠️ v3.4.1：空模拟账户必须走预检降级，禁止直接下单**
> 实测 `` 可能返回 `total:0`（未建仓/换设备），此时"模拟卖出"必然失败。
> 下单前**必须先做四步预检**，任一不过即降级为"方案输出 + 试单预检报告"，不产生成交记录：
>
> | 预检项 | 通过条件 | 不过时的处置 |
> |-------|---------|------------|
> | 代码格式 | `sh/sz/hk/us` + 数字 | 报错并提示正确格式 |
> | 市场可交易 | 沪深A股/港股通标的 | 剔除该标的，改用替代标的 |
> | 数量整数倍 | A股 100 股整数倍 | 向下取整到 100 的倍数 |
> | 持仓充足 | 可卖数量 ≥ 拟卖数量 | **降级**：输出减仓方案 + 标注"模拟账户无持仓，未执行试单" |
>
> 降级时报告须写明 `execution_status: "dry_run_only"` 与未成交原因，
> **不得**在 HTML 中渲染成"已执行"或"试单成功"。

## 输出文件
- 作战方案 HTML（含动作清单、时间线、置信度）
- 模拟交易记录（从 模拟撮合（本地 paper trading） 反查）

## 数据接口
| 工具 | 用途 |
|------|------|
| `fin_data.py news` + `fin_data.py notice` | 实时舆情 |
| `fin_data.py events` | 历史事件匹配 |
| `fin_data.py fund_flow` | 主力资金 |
| `fin_data.py north_holding` | 北向 |
| `fin_data.py fund_short` | 卖空 |
| `fin_data.py lhb` | 游资 |
| `fin_data.py disclosure` | 信披 |
| `fin_data.py sector` | 替代标的 |
| `模拟撮合（本地 paper trading）` | 模拟交易 |
| `本地模拟成交流水` | 交易历史 |
| `本地模拟持仓` | 模拟账户 |

## 版本
| 版本 | 日期 | 更新 |
|------|------|------|
| v1.0.0 | 2026-09-04 | 初版（5min流水线） |
| v3.0.0 | 2026-09-05 | 自动舆情 + 历史案例 + 模拟交易 + 一键执行 |
| **v3.2.0** | **2026-09-09** | **案例库落地 data/case_library.json（50条真实案例）+ 5分钟显式并行DAG与超时降级 + 减仓前合规可执行检查（EX规则）+ 人工确认闸门 auto_confirm + 分级采用 scoring.json 公式 + 输出含人话版** |
| **v3.2.1** | **2026-09-09** | **DAG/超时降级预算表写入正文 + Step 4 可执行性检查前置落地（读 rules.json executability）+ Step 5 人工确认闸门 auto_confirm 落地** |
| **v3.3.0** | **2026-10-21** | **✨ 新增 scripts/match_cases.py（案例库检索零依赖脚本化，输出 Top3 + 跌幅中位数 + 样本数，禁止 LLM 凭记忆举例）+ 分级改调 classify.py 脚本（修复 P0 不可达缺陷）+ 案例库 50 条/12 类数据完整性校验通过** |

## 路演亮点
- **现场模拟舆情**：演示时手动注入"佳缘科技造假"舆情
- **5min 出方案 + 模拟试单**：现场看到 模拟撮合（本地 paper trading） 真实运行
- **历史案例类比**：显示康美/康得新同期走势作为参考
- **一键执行**：路演时真实点击模拟单
| **v3.3.1** | **2026-10-22** | **📌 明示跨 skill 依赖：`classify.py` 属于 fin-ai-news，单装本 skill 时该命令会失败，给出降级路径 + 真实数据回归复测通过（财务造假类 12 例，中位数跌幅 -80%）** |
| **v3.3.2** | **2026-10-23** | **与团队 v3.3.2 契约对齐；案例库为活配置（配置绑定审计通过）** |
| **v3.4.0** | **2026-10-25** | **✨ 单装可用性修复：`classify.py` 改为内置转发壳（scripts/classify.py），只装本 skill 也能跑，不再因 ../fin-ai-news 路径不存在而失败；转发壳不含计算逻辑，改共用实现全队立即生效，无副本漂移 + 📝 修正展示层版本冲突（description 写「角色 v3.0」与 frontmatter 版本号不一致）** |
| **v3.4.1** | **2026-10-25** | **✨ `match_cases.py` 防高估三连：① severity 改相邻衰减打分，避免 P1 业绩事件被套到 P0 退市级案例；② 基准改为「同类型同严重度」优先，样本 <5 才逐级降级并标注 benchmark_level；③ 新增 impact_class 分层与**跨等级类比拦截**，并在输出内置 `estimation_guard`——明确禁止把历史 max_drop 直接当跌幅预测（宁德 Q3 环比 -5.8% 若直接套用旧中位 -35% 会高估约 6 倍）。案例库 50→56 例，补齐 earnings_shock 温和样本；新增 `dedup.py` 转发壳** |
| **v4.0.0** | **2026-10-25** | **🌍 开源版：移除私有连接器 westock-mcp 依赖，改用内置统一数据层 shared/fin_data.py（L1 公开源 / L2 AKShare / L3 yfinance，零 API Key）+ 中英双语文档** |
