"""Import equipment_model document metadata into the 4 knowledge datasets.

Root cause B: the "Retrieval - Selected Model" node filters on metadata
`equipment_model`, but that field was never imported into Dify - so every
request carrying a model name returned zero chunks.

Idempotent: existing fields are reused, values are upserted.
"""
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from uuid import uuid4

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost/v1"
FIELD = "equipment_model"

DATASETS = {
    "14f69bf6-8deb-4710-b5df-66e9edef6352": "manuals",
    "56c9585e-04cc-4e54-b171-7c6de6437b52": "sops",
    "680b6653-cefa-4e12-b633-7a91ce95aa13": "fault-cases",
    "1eda78d7-a791-4371-a3b4-55dcd73fc823": "parts",
}

TOKEN = subprocess.run(
    ["docker", "exec", "docker-api-1", "cat", "/tmp/dataset_token.txt"],
    capture_output=True, text=True, encoding="utf-8",
).stdout.strip()
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def pg(sql):
    return subprocess.run(
        ["docker", "exec", "docker-db_postgres-1", "psql", "-U", "postgres", "-d", "dify", "-t", "-A", "-F", "|", "-c", sql],
        capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()


meta = {}
with (ROOT / "data" / "dify-docs" / "metadata.csv").open(encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        meta[row["filename"]] = row["equipment_model"]

# document_id -> filename per dataset
docs = defaultdict(dict)
for line in pg("SELECT d.id, doc.id, doc.name FROM datasets d JOIN documents doc ON doc.dataset_id=d.id;").splitlines():
    if not line.strip():
        continue
    ds_id, doc_id, name = line.split("|")
    docs[ds_id][doc_id] = name

apply = "--apply" in sys.argv
print(f"datasets: {len(docs)}  field: {FIELD}  apply={apply}\n")

for ds_id in DATASETS:
    ds_docs = docs.get(ds_id, {})
    print("=" * 70)
    print(f"dataset {ds_id} ({DATASETS[ds_id]}) : {len(ds_docs)} documents")

    # 1. does the field already exist?
    r = requests.get(f"{BASE}/datasets/{ds_id}/metadata", headers=H, timeout=60)
    r.raise_for_status()
    existing = {m["name"]: m for m in r.json().get("doc_metadata", [])}
    if FIELD in existing:
        metadata_id = existing[FIELD]["id"]
        print(f"  field exists: {metadata_id}")
    else:
        print(f"  field '{FIELD}' missing -> creating")
        if apply:
            body = {"type": "string", "name": FIELD}
            rc = requests.post(f"{BASE}/datasets/{ds_id}/metadata", headers=H, json=body, timeout=60)
            print(f"    create HTTP {rc.status_code}")
            if rc.status_code not in (200, 201):
                print("   ", rc.text[:400])
                continue
            metadata_id = rc.json()["id"]
            print(f"    created: {metadata_id}")
        else:
            metadata_id = "<dry-run-id>"

    # 2. build operations
    values = Counter()
    ops = []
    unmatched = []
    for doc_id, name in ds_docs.items():
        if name not in meta:
            unmatched.append(name)
            continue
        value = meta[name]
        values[value] += 1
        ops.append({
            "document_id": doc_id,
            "metadata_list": [{"id": metadata_id, "name": FIELD, "value": value}],
            "partial_update": True,
        })
    print(f"  values: {dict(values)}")
    if unmatched:
        print(f"  UNMATCHED documents (no metadata.csv row): {unmatched}")
    print(f"  operations: {len(ops)}")

    if apply and ops:
        rc = requests.post(f"{BASE}/datasets/{ds_id}/documents/metadata",
                           headers=H, json={"operation_data": ops}, timeout=180)
        print(f"  bind HTTP {rc.status_code} {rc.text[:200]}")
