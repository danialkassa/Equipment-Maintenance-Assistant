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
