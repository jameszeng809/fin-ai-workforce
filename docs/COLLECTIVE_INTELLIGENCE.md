# 🧠 群体智能设计说明 · Collective Intelligence Design

> 这篇文档回答一个问题：**九个 Agent，凭什么叫「团队」？**
> This note answers one question: **when do nine agents deserve to be called a team?**

---

## 1. 我们反对什么 · What we are against

绝大多数多 Agent 系统做的是下图的左边：一个问题，N 个角色，N 份平行报告，最后拼在一起。**没有冲突，也没有真相**。

Most multi-agent systems look like the left side: one question, N roles, N parallel reports, concatenated at the end. **No conflict, no truth.**

```
❌ 错误示范 Anti-pattern              ✅ 我们的做法 Our approach
   问题 ─┬─► 角色A ─► 报告A             问题 ─► CIO 主理人
        ├─► 角色B ─► 报告B                      │
        └─► 角色C ─► 报告C                      ├─► 第1轮：独立陈述
                      │                        ├─► 第2轮：交叉质疑（可否决）
                      ▼                        ├─► 第3轮：收敛裁决
                    拼接                        └─► 共识度评分 + 分歧清单
             （谁也不反驳谁）                      （分歧被显式记录）
```

**差别在于：平行报告里，错误会平铺;圆桌讨论里，错误会被点名。**
Parallel reports let errors sit side by side. A roundtable names them.

---

## 2. 三轮圆桌会议 · The three-round roundtable

| 轮次 Round | 做什么 What happens | 为什么 Why |
|:---:|---|---|
| **1 · 独立陈述** | 8 名员工各自独立完成作业，互不可见 Independent work, no peeking | 避免锚定效应 anchor bias |
| **2 · 交叉质疑** | 互相审阅彼此结论，**有权否决** Review each other, **with veto power** | 制造建设性冲突 engineered conflict |
| **3 · 收敛裁决** | CIO 加权汇总，输出共识度与分歧点 Weighted aggregation with explicit dissent | 让不可调和的分歧可见 make dissent visible |

### 否决权矩阵 · Who can veto whom

| 否决方 Veto holder | 被否决对象 Target | 依据 Grounds |
|---|---|---|
| 🛡️ 风控官 Risk Officer | 🔬 研究员的估值结论 researcher's valuation | 下行情景、VaR 超限 downside / VaR breach |
| 📈 量化分析师 Quant | 📊 风控与估值的模型假设 model assumptions of both | β、协方差、因子暴露异常 bad β / covariance / exposure |
| ⚖️ 合规专员 Compliance | 🎯 整笔交易 the entire trade | 触发 `rules.json` 中的条款 rule ID triggered |
| 🎼 CIO 主理人 Orchestrator | 任何结论 any conclusion | 共识度低于阈值 consensus below threshold |

> 注意：**交易执行官没有被授予否决权**，也没有决策权。它只回答"怎么买更划算"。
> 决策权与执行权在架构上强制分离。
> The execution trader has **no veto and no decision right** — it only answers "how to buy efficiently".

---

## 3. 弃权机制：让 AI 学会说"我不知道" · The right to abstain

每个员工上报的 Signal 卡里都有 `abstain` 字段：

```json
{
  "value": -0.35,
  "confidence": 0.72,
  "abstain": false,
  "abstain_reason": null,
  "recommendation": "hold"
}
```

**当必需数据缺 ≥3 项时，员工必须 `abstain: true` 并写明原因**；主理人据此降低其表决权重，而不是把缺口抹平。

Missing ≥3 required inputs ⇒ `abstain: true` with a reason. The orchestrator then **down-weights** that vote rather than papering over the gap.

**为什么这很重要？**
在金融场景里，"我不知道"是有价值的输出。一个编出来的高置信度结论，比一次诚实的缺席危险得多。

In finance, "I don't know" is a valuable output. A fabricated high-confidence call is far more dangerous than an honest absence.

---

## 4. 共识度评分 · Consensus scoring

```python
# 概念版 pseudo-code, see fin-ai-orchestrator/scripts/consensus.py
weighted = Σ (weight_i × credibility_i × signal_i) / Σ (weight_i × credibility_i)
credibility_i = f(confidence_i, abstain_i, data_status_i, historical_accuracy_i)
```

其中 **数据状态直接进入可信度**：一次跑在 `degraded` 数据上的结论，权重自动下调。
`Data status feeds credibility`: a conclusion computed on `degraded` data is automatically down-weighted.

| 共识度 Consensus | 输出形态 Output form |
|---|---|
| 高 High | 明确操作建议 actionable recommendation |
| 中 Medium | 建议 + 显著位置标出分歧点 recommendation with dissent flagged |
| 低 Low | **自动降级为「观察名单」**，不强行给结论 downgraded to *watchlist* |

低共识时强行给结论，是很多 Agent 系统最危险的行为。**我们选择不给。**
Forcing a verdict at low consensus is the most dangerous behaviour in agent systems. **We decline.**

---

## 5. 数据契约：让协作可编程 · The shared contract

九名员工之间不互相传"话"，而是传**同一份 JSON**：

Employees do not exchange prose; they exchange **one JSON contract**:

```json
{
  "schema_version": "4.0.0",
  "skill_id": "fin-ai-researcher",
  "signal": { "value": -0.35, "confidence": 0.72, "abstain": false },
  "audit":  { "data_as_of": "2026-10-25", "downgraded_sources": [], "input_snapshot_hash": "sha256:…" },
  "payload": { "valuation": { "dcf": 1295.9 }, "verdict": "合理偏低估" }
}
```

三个字段让整个系统**可审计**：

| 字段 Field | 作用 Purpose |
|---|---|
| `audit.downgraded_sources` | 哪些数据降级了 which inputs were degraded |
| `audit.input_snapshot_hash` | 决策可回放 decision replayable |
| `signal.abstain_reason` | 为什么弃权 why it abstained |

所有上报前必须通过校验器（`fin-ai-orchestrator/scripts/validate_package.py`），
**过不了校验的结论禁止上报**。
Every submission is validated before escalation. If it fails validation, it must not be escalated.

---

## 6. 一个真实片段 · A real episode

在一次针对某白酒龙头的投委会运行中：

1. **研究员** 跑 DCF 得每股内在价值 ¥1295.9，较现价 ¥1335 偏离 -2.93%，初判"合理偏低估"；
2. **量化分析师** 复核发现 β 回归 = **-0.20**、R² = **0.033**，宣布该 β 不可用 → 触发 `dcf.py` **护栏**（WACC 0.55% < g 3%）；
3. **研究员** 因此把 DCF 降为"参考区间"，主结论改用相对估值（PE 历史分位 + 可比公司）；
4. **风控官** 给出 β 不可用下的替代波动假设，并叠加行业下行情景，输出受限后的仓位上限；
5. **合规专员** 未触发任何条款 → 放行；
6. **CIO** 汇总：共识度 **中等**，因为"DCF 口径 unavailable"被显式计入分歧项，最终输出"观察 + 分批"，而非"买入"。

> 整条链路里，**没有一个 Agent 假装自己拿到了数据**。这是我们希望评审团重点看的地方。
> Along this chain, **no agent pretended to have data it did not have**. That is the part we want judges to look at.

---

## 7. 对比一览 · Comparison

| 维度 Dimension | 平行报告式 Parallel-report agent | 本团队 This team |
|---|---|---|
| 冲突处理 Conflict | 无，各说各话 ignored | 交叉质疑 + 否决权 cross-examination + veto |
| 数据缺口 Data gaps | 估算补齐 silently filled | `abstain` + 显式披露 declared |
| 结论强度 Verdict | 永远给结论 always gives one | 低共识自动降级 auto-downgrade |
| 可审计性 Auditability | 自然语言 reason in prose | JSON 契约 + 哈希 schema + hash |
| 角色权力 Power | 人人平等 all equal | 写作权 ≠ 否决权 ≠ 执行权 separated |

---

## 8. 一句话 Summary

> **群体智能不是把九个答案加起来，而是让它们学会互相否决，并且有权承认无知。**
> **Collective intelligence is not adding nine answers up — it is letting them veto each other and admit ignorance.**
