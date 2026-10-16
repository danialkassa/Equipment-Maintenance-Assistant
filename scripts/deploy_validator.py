"""Deploy the corrected validator code into the Dify code node and publish."""
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validator_fixed import CODE  # noqa: E402

BASE = "http://localhost/console/api"
APP_ID = "5527f4d0-995c-4318-b3cd-90fc08af1585"
CODE_ID = "1791705483005"

TOKEN = subprocess.run(["docker", "exec", "docker-api-1", "cat", "/tmp/admin_token.txt"],
                       capture_output=True, text=True, encoding="utf-8").stdout.strip()
CSRF = subprocess.run(["docker", "exec", "docker-api-1", "cat", "/tmp/csrf_token.txt"],
                      capture_output=True, text=True, encoding="utf-8").stdout.strip()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "X-CSRF-Token": CSRF}
COOKIES = {"csrf_token": CSRF, "__Host-csrf_token": CSRF, "access_token": TOKEN, "__Host-access_token": TOKEN}


def main(apply):
    draft = requests.get(f"{BASE}/apps/{APP_ID}/workflows/draft", headers=H, cookies=COOKIES, timeout=60).json()
    graph = draft["graph"]
    node = next((n for n in graph["nodes"] if n["id"] == CODE_ID), None)
    if node is None:
        print("ERROR: code node not found")
        return 1
    old = node["data"].get("code", "")
    print(f"old code: {len(old)} chars")
    print(f"new code: {len(CODE)} chars")
    print("old checks for placeholders:", "资料未提及" in old)
    print("new checks for placeholders:", "资料未提及" in CODE)
    node["data"]["code"] = CODE
    # outputs declared on the node must keep matching the function's return keys
    print("declared outputs:", list(node["data"].get("outputs", {}).keys()))

    if not apply:
        print("\nDRY RUN. Use --apply")
        return 0

    body = {
        "graph": graph,
        "features": draft.get("features", {}),
        "conversation_variables": draft.get("conversation_variables", []),
        "hash": draft.get("hash"),
    }
    r = requests.post(f"{BASE}/apps/{APP_ID}/workflows/draft", headers=H, cookies=COOKIES, json=body, timeout=120)
    print(f"SAVE draft: HTTP {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        return 1
    r2 = requests.post(f"{BASE}/apps/{APP_ID}/workflows/publish", headers=H, cookies=COOKIES, timeout=120)
    print(f"PUBLISH: HTTP {r2.status_code} {r2.text[:200]}")
    return 0 if r2.status_code == 200 else 1


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
