#!/usr/bin/env bash
# =====================================================================
# Creates the evaluation project folders/files for the Dify project
# Run in Git Bash:  bash create-eval-project.sh
# =====================================================================
set -e

# Project root = parent of the setup/ folder where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
mkdir -p "$ROOT/scripts" "$ROOT/tests" "$ROOT/docs/screenshots" "$ROOT/dsl"
cd "$ROOT"

# ---------------------------------------------------------------------
# .env  (paste your real API keys after publishing the apps)
# ---------------------------------------------------------------------
cat > .env <<'EOF'
DIFY_CHATFLOW_KEY=app-PASTE_CHATFLOW_KEY_HERE
DIFY_BASE_URL=http://localhost/v1
EOF

cat > requirements.txt <<'EOF'
requests
python-dotenv
EOF

cat > .gitignore <<'EOF'
.env
.env.local
__pycache__/
*.pyc
*.pyo
node_modules/
.DS_Store
*.log
EOF

# ---------------------------------------------------------------------
# tests/test_cases.csv  (last field quoted because it contains commas)
# ---------------------------------------------------------------------
cat > tests/test_cases.csv <<'EOF'
id,question,equipment_model,expected_keywords
1,JX-2000A液压压力不足,JX-2000A,"溢流阀,泵,压力"
2,JX-3000B发动机启动困难,JX-3000B,"启动,燃油,点火"
3,E05报警代码,,"E05,超载,传感器"
4,液压油多久换一次,,"液压油,更换,周期"
5,传感器校准失败,JX-2000A,"校准,零偏,IMU"
6,泵有异常噪音,JX-3000A,"泵,噪音,轴承"
7,系统压力波动大,,"压力,波动,溢流"
8,油温过高,JX-2000A,"油温,散热,冷却"
9,JX-2000A-047是什么零件,,"JX-2000A-047,备件"
10,预防性维护周期,,"维护,周期,检查"
11,溢流阀怎么调节,,"溢流阀,调节,压力"
12,导航模块初始化失败,NX-100,"导航,初始化,IMU"
13,今天天气,,
14,我不清楚,,
15,JX-2000A和JX-3000B的区别,,"JX-2000A,JX-3000B,区别"
16,JX-2000A更换液压油步骤,JX-2000A,"液压油,排空,加注"
17,发动机水温过高,JX-3000B,"水温,冷却,节温器"
18,系统报错E12,,"E12,错误"
19,振动传感器读数异常,JX-2000A,"振动,传感器"
20,备用电源无法启动,,"电源,启动,电池"
21,如何检测液压油质,,"液压油,检测,污染"
22,JX-3000B油泵异响,JX-3000B,"油泵,异响"
23,控制面板黑屏,,"面板,屏幕,电源"
24,JX-2000A保养周期,JX-2000A,"保养,周期,保养项"
25,液压系统漏油,,"液压,漏油,密封"
26,发动机冒黑烟,JX-3000B,"黑烟,燃油,燃烧"
27,压力传感器校准,,"压力传感器,校准"
28,JX-2000A-012备件库存,,"JX-2000A-012,库存"
29,系统无法连接网络,,"网络,连接"
30,液压泵不工作,JX-2000A,"液压泵,工作"
31,温度传感器报警,,"温度传感器,报警"
32,发动机机油压力低,JX-3000B,"机油,压力"
33,如何更换空气滤芯,,"空气滤芯,更换"
34,液压油颜色变黑,JX-2000A,"液压油,颜色"
35,系统响应缓慢,,"系统,响应,缓慢"
36,备用电池更换周期,,"备用电池,更换"
37,JX-2000A噪音异常,JX-2000A,"噪音,异常"
38,发动机启动后熄火,JX-3000B,"启动,熄火"
39,液压缸动作缓慢,JX-2000A,"液压缸,动作"
40,遥控器无响应,,"遥控器,响应"
EOF

# ---------------------------------------------------------------------
# scripts/run_evaluation.py
# ---------------------------------------------------------------------
cat > scripts/run_evaluation.py <<'EOF'
import os
import csv
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CHATFLOW_KEY = os.environ["DIFY_CHATFLOW_KEY"]
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost/v1")

def call_chatflow(question, model=""):
    url = f"{BASE_URL}/chat-messages"
    headers = {"Authorization": f"Bearer {CHATFLOW_KEY}", "Content-Type": "application/json"}
    body = {
        "inputs": {"equipment_model": model},
        "query": question,
        "user": "eval",
        "response_mode": "blocking",
    }
    start = time.time()
    try:
        r = requests.post(url, headers=headers, json=body, timeout=90)
        elapsed = time.time() - start
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "latency": round(elapsed, 2)}
        data = r.json()
        usage = data.get("metadata", {}).get("usage", {})
        return {
            "answer": data.get("answer", ""),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency": round(elapsed, 2),
        }
    except Exception as e:
        return {"error": str(e), "latency": round(time.time() - start, 2)}

def main():
    with open("../tests/test_cases.csv", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['question'][:40]}")
        result = call_chatflow(case["question"], case.get("equipment_model", ""))
        expected = [k.strip() for k in case["expected_keywords"].split(",") if k.strip()]
        answer = result.get("answer", "")
        hits = sum(1 for kw in expected if kw in answer)
        # Negative cases (no expected keywords) must be checked manually.
        passed = (hits >= max(1, len(expected) // 2)) if expected else False
        result.update({
            "id": case["id"],
            "question": case["question"],
            "expected_keywords": case["expected_keywords"],
            "hits": hits,
            "total_expected": len(expected),
            "passed": passed,
        })
        results.append(result)
        time.sleep(0.5)

    with open("../docs/test-results.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    judged = [r for r in results if r["total_expected"] > 0]
    passed = sum(1 for r in judged if r["passed"])
    avg_lat = sum(r["latency"] for r in results) / len(results)
    total_tok = sum(r.get("total_tokens", 0) for r in results)
    print(f"\nPassed (auto-judged): {passed}/{len(judged)} ({100*passed//len(judged)}%)")
    print("2 negative cases (13, 14) need a manual check: fallback answer = pass")
    print(f"Avg latency: {avg_lat:.2f}s")
    print(f"Total tokens: {total_tok}")

if __name__ == "__main__":
    main()
EOF

echo ""
echo "Done. Project created at: $ROOT"
find "$ROOT" -type f | sort
