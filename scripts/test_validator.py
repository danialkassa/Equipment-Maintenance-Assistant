"""Test the corrected validator: it must reject non-answers and accept real ones."""
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validator_fixed import CODE  # noqa: E402

# --- try to execute the validator locally ------------------------------------
namespace = {}
try:
    exec(CODE, namespace)
    main = namespace["main"]
    print("validator executed locally (host Python)\n")
    LOCAL = True
except Exception as exc:  # pragma: no cover
    print("host exec failed:", exc)
    LOCAL = False


def run_local(payload):
    return main(payload)


def run_sandbox(payload):
    """Execute through Dify's own code sandbox so we test the real runtime."""
    body = {"code": CODE, "language": "python3", "inputs": {"llm_output": payload}}
    r = requests.post("http://localhost:8194/v1/sandbox/run", headers={"X-Api-Key": "dify-sandbox"}, json=body, timeout=60)
    return r


GOOD = {
    "possible_causes": ["溢流阀调节弹簧疲劳导致开启压力下降（manual-03.txt）", "液压泵存在内泄（fault-01.txt）"],
    "diagnostic_steps": ["检查溢流阀开启压力是否低于18 MPa（manual-01.txt）"],
    "repair_procedure": ["更换溢流阀总成并按 SOP-03 调节至 16 MPa（sop-03.txt）"],
    "safety_warnings": ["停机泄压后由授权人员操作"],
    "source_documents": ["manual-03.txt", "fault-01.txt", "sop-03.txt"],
}

ALL_PLACEHOLDER = {
    "possible_causes": ["资料未提及"],
    "diagnostic_steps": ["资料未提及"],
    "repair_procedure": ["资料未提及"],
    "safety_warnings": ["无"],
    "source_documents": ["资料未提及"],
}

CASES = []
CASES.append(("real grounded answer -> valid", GOOD, True))
CASES.append(("全部资料未提及 (the reported bug) -> invalid", ALL_PLACEHOLDER, False))

# source_documents must always name a real document
bad = json.loads(json.dumps(GOOD))
bad["source_documents"] = ["资料未提及"]
CASES.append(("source_documents = 资料未提及 -> invalid", bad, False))
bad = json.loads(json.dumps(GOOD))
bad["source_documents"] = []
CASES.append(("source_documents empty -> invalid", bad, False))
bad = json.loads(json.dumps(GOOD))
del bad["source_documents"]
CASES.append(("source_documents missing -> invalid", bad, False))
bad = json.loads(json.dumps(GOOD))
bad["source_documents"] = ["未找到相关技术资料"]
CASES.append(("source_documents = marker -> invalid", bad, False))
bad = json.loads(json.dumps(GOOD))
bad["source_documents"] = ["已参考相关文档", "见上文"]
CASES.append(("source_documents names no real doc -> invalid", bad, False))

# Regression: case 42 produced this shape - a marker plus a long qualifying tail.
# The model refused the unsafe request but dressed it as an answer, and the
# validator must not present that as a grounded diagnosis.
bad = json.loads(json.dumps(GOOD))
bad["source_documents"] = ["资料未提及“远程关机”功能说明，无法据此定位原因（manual-14.txt）"]
CASES.append(("source_documents = marker + refusal tail -> invalid", bad, False))

# A genuinely cited short document name must still pass.
good_short = json.loads(json.dumps(GOOD))
good_short["source_documents"] = ["manual-12.txt", "sop-01.txt"]
CASES.append(("short but real document names -> valid", good_short, True))

# a single substantive content field is enough (partial but grounded answer)
for field in ("possible_causes", "diagnostic_steps", "repair_procedure"):
    partial = json.loads(json.dumps(GOOD))
    for other in ("possible_causes", "diagnostic_steps", "repair_procedure"):
        if other != field:
            partial[other] = ["资料未提及"]
    CASES.append((f"only {field} substantive -> valid (partial)", partial, True))

# every content field ungrounded -> invalid
bad = json.loads(json.dumps(GOOD))
for field in ("possible_causes", "diagnostic_steps", "repair_procedure"):
    bad[field] = ["资料未提及"]
CASES.append(("all content fields ungrounded -> invalid", bad, False))

for marker in ["未找到相关技术资料", "无相关信息", "no relevant information", "Not available in the provided documents", "N/A", "无", "  "]:
    bad = json.loads(json.dumps(GOOD))
    for f in ("possible_causes", "diagnostic_steps", "repair_procedure"):
        bad[f] = [marker]
    CASES.append((f"all content = {marker!r} -> invalid", bad, False))

CASES.append(("empty string -> invalid", "", False))
CASES.append(("None -> invalid", None, False))
CASES.append(("garbage text -> invalid", "not json at all", False))
CASES.append(("JSON list -> invalid", [1, 2, 3], False))
CASES.append(("valid JSON string payload -> valid", json.dumps(GOOD, ensure_ascii=False), True))
CASES.append(("fenced JSON -> valid", "```json\n" + json.dumps(GOOD, ensure_ascii=False) + "\n```", True))
CASES.append(("prose + JSON -> valid", "好的，结果如下：\n" + json.dumps(GOOD, ensure_ascii=False), True))

aliased = {
    "可能原因": ["溢流阀弹簧疲劳（manual-03.txt）"],
    "诊断步骤": ["检查溢流阀（manual-01.txt）"],
    "维修流程": ["更换溢流阀（sop-03.txt）"],
    "安全警告": ["无"],
    "参考文档": ["manual-03.txt"],
}
CASES.append(("Chinese aliases -> valid", aliased, True))

if LOCAL:
    print("=" * 78)
    failures = 0
    for label, payload, expect_valid in CASES:
        out = run_local(payload)
        keys_ok = set(out or {}) == {"valid", "answer_md", "error"}
        got = (out or {}).get("valid")
        ok = got == ("true" if expect_valid else "false") and keys_ok
        if not ok:
            failures += 1
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        print(f"        valid={got} error={out.get('error')!r} keys_ok={keys_ok}")
    print("=" * 78)
    print(f"local results: {len(CASES) - failures}/{len(CASES)} passed")

    print("\n--- rendered markdown for the good case ---")
    print(run_local(GOOD)["answer_md"])

    # --- control: show the ORIGINAL buggy validator accepts the non-answer ---
    print("\n--- control: original validator on the same non-answer ---")
    ORIGINAL = r'''
def main(llm_output):
    import json
    if not llm_output:
        return {"valid": "false", "answer_md": "", "error": "empty_output"}
    try:
        data = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
    except Exception:
        return {"valid": "false", "answer_md": "", "error": "parse_failed"}
    if not isinstance(data, dict):
        return {"valid": "false", "answer_md": "", "error": "not_an_object"}
    required = ["possible_causes", "diagnostic_steps", "repair_procedure", "source_documents"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return {"valid": "false", "answer_md": "", "error": "missing: " + ",".join(missing)}
    md = "## 可能原因\n" + "\n".join(f"- {x}" for x in data["possible_causes"])
    md += "\n\n## 诊断步骤\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(data["diagnostic_steps"], 1))
    md += "\n\n## 维修流程\n" + "\n".join(f"{i}. {x}" for i, x in enumerate(data["repair_procedure"], 1))
    sw = data.get("safety_warnings") or ["无"]
    md += "\n\n## 安全警告\n" + "\n".join(f"- {x}" for x in sw)
    md += "\n\n## 参考文档\n" + "\n".join(f"- {x}" for x in data["source_documents"])
    return {"valid": "true", "answer_md": md, "error": ""}
'''
    ns2 = {}
    exec(ORIGINAL, ns2)
    old_out = ns2["main"](ALL_PLACEHOLDER)
    print("original valid =", old_out["valid"], "(BUG: non-answer passes)")
    new_out = main(ALL_PLACEHOLDER)
    print("corrected valid =", new_out["valid"], "error =", repr(new_out["error"]))
