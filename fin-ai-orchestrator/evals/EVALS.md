# evals · 团队质量评测用例（v3.2.0）

> 用途：发布前回归测试。3 个用例覆盖计算正确性、边界行为、归因守恒。
> 每个用例给出固定输入与期望输出断言，发布前必须全部通过。

## 用例 1 · VaR 蒙特卡洛（fin-ai-risk/scripts/var.py）

**输入**（固定种子 42，结果确定）：
```
python scripts/var.py --weights 0.5,0.5 --vols 0.25,0.25 --corr "1,0.5;0.5,1" --n 10000
```
**断言**：
- `var_95_1d` ∈ [0.020, 0.028]（两资产日波动≈0.25/√244≈0.016，组合相关 0.5 → 组合日波动≈0.0139，95% 分位≈2.3%）【实测 0.0228，PASS】
- `cvar_99_1d` > `var_99_1d`（CVaR 必须 > VaR，尾部更重）
- `var_95_10d` ≈ `var_95_1d` × √10（±5%）

## 用例 2 · DDM 低股息必须 N/A（fin-ai-researcher Step7.3 边界行为）

**输入**：某股 dividend_yield = 0.8%（<1.5% 阈值）
**断言**：
- 估值汇总中 `ddm` 字段必须为字符串 `"N/A"`，禁止输出任何数值
- 报告必须提示"分红率偏低，建议参考 DCF 为主"
- **反向断言**：dividend_yield = 5% 时 DDM 正常输出数值

## 用例 3 · Brinson 归因守恒（fin-ai-portfolio/scripts/brinson.py）

**输入**：
```
python scripts/brinson.py --pw 0.6,0.4 --bw 0.5,0.5 --pr 0.12,0.06 --br 0.10,0.04 --sectors 消费,科技
```
**断言**：
- `summary.excess_return` = 0.6×0.12+0.4×0.06 − 0.5×0.10−0.5×0.04 = 0.0200（±1e-4）
- `conservation_check` 绝对值 < 1e-4
- 配置+选股+交互 三项之和 = excess_return
- **反例断言**：`--pw 0.6,0.3`（权重和≠1）必须报错退出，禁止输出结果

## 运行方式

```bash
# 每次发布前在仓库根目录执行三个用例，全部 PASS 才允许发布
cd fin-ai-risk && python scripts/var.py --weights 0.5,0.5 --vols 0.25,0.25 --corr "1,0.5;0.5,1" --n 10000
cd ../fin-ai-portfolio && python scripts/brinson.py --pw 0.6,0.4 --bw 0.5,0.5 --pr 0.12,0.06 --br 0.10,0.04 --sectors 消费,科技
# 用例 2 为行为断言，由研究员 SKILL 执行时自查（LLM checklist）
```
