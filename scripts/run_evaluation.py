import os
import csv
import argparse
import json
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CHATFLOW_KEY = os.environ["DIFY_CHATFLOW_KEY"]
BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost/v1")
TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
FALLBACK_MARKERS = (
    "未找到相关技术资料",
    "请提供装备型号",
    "No relevant technical document found",
    "回答生成失败",
    "Answer generation failed",
    "资料未提及",
)


def call_chatflow(question, model="", retries=2):
    url = f"{BASE_URL}/chat-messages"
    headers = {"Authorization": f"Bearer {CHATFLOW_KEY}", "Content-Type": "application/json"}
    body = {
        "inputs": {"equipment_model": model},
        "query": question,
        "user": "eval",
        "response_mode": "blocking",
    }
    started = time.time()
    attempts = 0
    for attempt in range(retries + 1):
        attempts = attempt + 1
        try:
            response = requests.post(url, headers=headers, json=body, timeout=90)
            if response.status_code == 200:
                data = response.json()
                usage = data.get("metadata", {}).get("usage", {})
                return {
                    "answer": data.get("answer", ""),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "latency": round(time.time() - started, 2),
                    "attempts": attempts,
                }
            error = f"HTTP {response.status_code}"
            if response.status_code not in TRANSIENT_STATUS_CODES:
                break
        except (requests.RequestException, ValueError) as exception:
            error = str(exception)
        if attempt < retries:
            time.sleep(2 ** attempt)
    return {
        "error": error,
        "latency": round(time.time() - started, 2),
        "attempts": attempts,
    }


def evaluate_case(case, result):
    expected = [keyword.strip() for keyword in case["expected_keywords"].split(",") if keyword.strip()]
    answer = result.get("answer", "")
    hits = sum(1 for keyword in expected if keyword in answer)
    if expected:
        passed = hits >= max(1, (len(expected) + 1) // 2)
        category = "positive"
    else:
        passed = bool(answer) and any(marker in answer for marker in FALLBACK_MARKERS)
        category = "negative"
    return {
        "id": case["id"],
        "question": case["question"],
        "expected_keywords": case["expected_keywords"],
        "hits": hits,
        "total_expected": len(expected),
        "category": category,
        "passed": passed,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Equipment Maintenance Assistant chatflow.")
    parser.add_argument("--input", type=Path, default=ROOT / "tests" / "test_cases.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "test-results.csv")
    parser.add_argument("--summary", type=Path, default=ROOT / "docs" / "evaluation-summary.json")
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--min-positive-pass-rate", type=float, default=0.8)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['question'][:40]}")
        result = call_chatflow(case["question"], case.get("equipment_model", ""), args.retries)
        result.update(evaluate_case(case, result))
        results.append(result)
        time.sleep(args.delay)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    positive = [result for result in results if result["category"] == "positive"]
    negative = [result for result in results if result["category"] == "negative"]
    positive_passed = sum(1 for result in positive if result["passed"])
    negative_passed = sum(1 for result in negative if result["passed"])
    avg_lat = sum(r["latency"] for r in results) / len(results)
    total_tok = sum(r.get("total_tokens", 0) for r in results)
    positive_rate = positive_passed / len(positive) if positive else 0
    summary = {
        "positive_passed": positive_passed,
        "positive_total": len(positive),
        "positive_pass_rate": round(positive_rate, 4),
        "negative_passed": negative_passed,
        "negative_total": len(negative),
        "average_latency_seconds": round(avg_lat, 2),
        "total_tokens": total_tok,
        "acceptance_threshold": args.min_positive_pass_rate,
        "accepted": positive_rate >= args.min_positive_pass_rate and negative_passed == len(negative),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nPositive cases: {positive_passed}/{len(positive)} ({positive_rate:.0%})")
    print(f"Negative fallback cases: {negative_passed}/{len(negative)}")
    print(f"Avg latency: {avg_lat:.2f}s")
    print(f"Total tokens: {total_tok}")
    print(f"Acceptance: {'PASS' if summary['accepted'] else 'FAIL'}")
    return 0 if summary["accepted"] else 1

if __name__ == "__main__":
    sys.exit(main())
