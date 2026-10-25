#!/usr/bin/env python3
"""团队作战包校验器：校验 9 名员工输出是否符合 shared 数据契约。

用途：fin-ai-orchestrator Step3 收集团队作战包后的强制校验步骤（反馈回路：
      校验 → 不通过则打回对应员工重跑 → 重试最多 1 次）。
依赖：无第三方依赖（内置轻量校验，避免 jsonschema 环境差异）
用法：python scripts/validate_package.py package.json
      python scripts/validate_package.py package.json --hash snapshot.json
输出：PASS / FAIL + 明细（--json 可输出机器可读结果）

v3.4.1 修正：所有输出（含错误）统一写 **stdout**。旧版 `sys.exit(str)` 把错误打到 stderr，
而现场最常见的用法是 `validate_package.py pkg.json | jq` 或由编排脚本 json.loads(stdout)——
出错时 stdout 为空，调用方会误判为「通过但无内容」，契约层的失败被静默吞掉。

v3.3.0 修正：schema_version 不再硬编码单一常量（旧版只认 3.2.0，导致 3.2.2/3.2.3
员工输出被误判 FAIL），改为契约版本白名单；并补齐 schema 中已声明但旧版未实现的
skill_id / subject.type / signal.recommendation 枚举校验。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "..", "data", "team_package.schema.json")

# 内置兜底（schema 文件缺失/损坏时使用）
REQUIRED_TOP = ["schema_version", "skill_id", "timestamp", "subject", "signal", "audit"]
REQUIRED_SIGNAL = ["value", "confidence", "reasoning"]
REQUIRED_AUDIT = ["input_snapshot_hash", "data_as_of"]


def load_schema():
    """v3.3.2：从 data/team_package.schema.json 读取必填字段与枚举。

    旧版把 required / 枚举全部硬编码在脚本里，schema 文件只是"说明书"——
    改了 schema 校验行为完全不变，合同与实现可能悄悄分叉。
    """
    try:
        with open(SCHEMA, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return None, f"无法读取 {SCHEMA}，已回退内置规则"
    props = s.get("properties", {})
    req = s.get("required") or REQUIRED_TOP
    sig = (props.get("signal", {}).get("required")) or REQUIRED_SIGNAL
    aud = (props.get("audit", {}).get("required")) or REQUIRED_AUDIT
    return {
        "required_top": req,
        "required_signal": sig,
        "required_audit": aud,
        "subject_types": props.get("subject", {}).get("properties", {}).get(
            "type", {}).get("enum"),
        "recommendations": props.get("signal", {}).get("properties", {}).get(
            "recommendation", {}).get("enum"),
    }, None
# v3.3.1：不再用「白名单硬编码」判版本。历史教训——v3.2.x 因白名单只写 3.2.0 导致
# 全部作战包误判 FAIL、圆桌收包断裂。现在改为「格式合法即通过」：
# 形如 X.Y.Z 的语义化版本一律接受，仅对「高于本校验器版本」的发出 warn，绝不阻断圆桌。
CURRENT_SCHEMA_VERSION = "3.4.1"
SUPPORTED_SCHEMA_VERSIONS = ["3.2.0", "3.2.1", "3.2.2", "3.2.3", "3.3.0", "3.3.1",
                             "3.3.2", "3.4.0", "3.4.1"]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SKILL_ID_PATTERN = re.compile(r"^fin-ai-[a-z]+$")
SUBJECT_TYPES = {"stock", "portfolio", "event"}
RECOMMENDATIONS = {"buy", "add", "hold", "reduce", "sell", "avoid", "partial_reduce"}
ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def emit(text, code=1):
    """统一把结果/错误写到 **stdout**（v3.4.1）。

    旧版错误走 sys.exit(str) → 打到 stderr。现场常见用法是
    `validate_package.py pkg.json | jq` 或用脚本 json.loads(stdout)，
    一旦出错 stdout 为空，调用方会把它当成"成功但没内容"，错误被吞掉。
    """
    print(text)
    sys.exit(code)


def main():
    args = [a for a in sys.argv[1:]]
    json_mode = "--json" in args
    args = [a for a in args if a != "--json"]
    if not args:
        emit("usage: python scripts/validate_package.py package.json "
             "[--hash snapshot.json] [--json]", code=2)
    try:
        with open(args[0], encoding="utf-8") as f:
            pkg = json.load(f)
    except Exception as e:
        if json_mode:
            emit(json.dumps({"result": "FAIL",
                             "errors": [f"无法读取或解析 JSON: {e}"],
                             "warnings": []}, ensure_ascii=False))
        emit(f"FAIL: 无法读取或解析 JSON: {e}")

    errors, warns = [], []
    S, schema_note = load_schema()
    if schema_note:
        warns.append(schema_note)
    REQ_TOP = S["required_top"] if S else REQUIRED_TOP
    REQ_SIG = S["required_signal"] if S else REQUIRED_SIGNAL
    REQ_AUD = S["required_audit"] if S else REQUIRED_AUDIT
    TYPES = set(S["subject_types"]) if (S and S.get("subject_types")) else SUBJECT_TYPES
    RECS = set(x for x in (S["recommendations"] if S else None) or [] if x is not None) \
        or RECOMMENDATIONS

    for k in REQ_TOP:
        if k not in pkg:
            errors.append(f"缺少顶层字段 {k}")

    sv = pkg.get("schema_version")
    if sv is not None:
        if not isinstance(sv, str) or not SEMVER.match(sv):
            errors.append(f"schema_version {sv!r} 格式非法，须为 X.Y.Z 语义化版本")
        else:
            def vt(s):
                return tuple(int(x) for x in s.split("."))
            if sv not in SUPPORTED_SCHEMA_VERSIONS:
                if vt(sv) > vt(CURRENT_SCHEMA_VERSION):
                    warns.append(f"schema_version {sv} 高于本校验器版本 "
                                 f"{CURRENT_SCHEMA_VERSION}，可能有新增字段未被校验（不阻断）")
                else:
                    warns.append(f"schema_version {sv} 为旧版本，请确认字段兼容（不阻断）")

    sid = pkg.get("skill_id")
    if isinstance(sid, str) and not SKILL_ID_PATTERN.match(sid):
        errors.append(f"skill_id {sid!r} 不符合 ^fin-ai-[a-z]+$")

    ts = pkg.get("timestamp")
    if isinstance(ts, str) and not ISO_TS.match(ts):
        warns.append(f"timestamp {ts!r} 非标准 ISO8601（建议 YYYY-MM-DDTHH:MM:SS）")

    subj = pkg.get("subject")
    if isinstance(subj, dict):
        if "type" not in subj:
            errors.append("subject 缺少 type")
        elif subj["type"] not in SUBJECT_TYPES:
            errors.append(f"subject.type {subj['type']!r} 不在 {sorted(SUBJECT_TYPES)} 内")
    elif subj is not None:
        errors.append("subject 必须是对象")

    sig = pkg.get("signal", {})
    if not isinstance(sig, dict):
        errors.append("signal 必须是对象")
        sig = {}
    else:
        for k in REQ_SIG:
            if k not in sig:
                errors.append(f"signal 缺少 {k}")
        if "value" in sig and not (isinstance(sig["value"], (int, float))
                                   and -1 <= sig["value"] <= 1):
            errors.append("signal.value 必须是 [-1, 1] 的数值")
        if sig.get("confidence") is not None and not (
                isinstance(sig["confidence"], (int, float)) and 0 <= sig["confidence"] <= 1):
            errors.append("signal.confidence 必须在 [0, 1]")
        if "reasoning" in sig and len(str(sig["reasoning"])) < 20:
            errors.append("reasoning 过短（<20 字），禁止空泛论据")
        if sig.get("abstain") and not sig.get("abstain_reason"):
            errors.append("abstain=true 时必须给出 abstain_reason")
        rec = sig.get("recommendation")
        if rec is not None and rec not in RECS:
            errors.append(f"signal.recommendation {rec!r} 不在 {sorted(RECS)} 内")

    audit = pkg.get("audit", {})
    if not isinstance(audit, dict):
        errors.append("audit 必须是对象")
        audit = {}
    else:
        for k in REQ_AUD:
            if k not in audit:
                errors.append(f"audit 缺少 {k}（防前视偏差必需）")
        if audit.get("downgraded_sources") and not isinstance(audit["downgraded_sources"], list):
            errors.append("audit.downgraded_sources 必须是数组")

    # 数据快照 hash 自洽性：允许调用方传入 --hash 交叉验证
    if len(args) > 2 and args[1] == "--hash":
        try:
            actual = hashlib.sha256(open(args[2], "rb").read()).hexdigest()[:16]
        except OSError as e:
            errors.append(f"无法读取快照文件: {e}")
        else:
            if audit.get("input_snapshot_hash") and \
                    not str(audit["input_snapshot_hash"]).startswith(actual[:8]):
                errors.append("输入快照 hash 与实际文件不符")

    ok = not errors
    if json_mode:
        print(json.dumps({"result": "PASS" if ok else "FAIL",
                          "errors": errors, "warnings": warns}, ensure_ascii=False))
        sys.exit(0 if ok else 1)
    for w in warns:
        print(f"WARN  - {w}")
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS")

if __name__ == "__main__":
    main()
