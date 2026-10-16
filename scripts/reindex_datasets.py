"""Re-index the four knowledge datasets so a document title stays with its body.

Why: the datasets were segmented on "\\n\\n" (blank-line) rules, which isolates
each document's title line into its own segment. Of 148 segments, 99 were under
60 characters, and a 13-character header such as "备件编号 名称 规格 库存" scores
0.741 against an unrelated query because a near-meaningless string embeds close
to the centroid of the vector space. Those centroid-like segments crowd real
content out of the top_k results, so the model answers "资料未提及".

Fix: switch the separator to "\\n" with a large max_tokens, so every short
document becomes a single segment containing its title and its content.

How re-indexing works in Dify 1.17:
  1. a new DatasetProcessRule row holds the new chunking settings;
  2. each document's `dataset_process_rule_id` must point at that row - Dify
     reuses the rule recorded on the document, not the dataset's latest one;
  3. the document must be put back to indexing_status='waiting', because the
     console retry endpoint refuses documents already 'completed';
  4. POST /console/api/datasets/<id>/retry re-runs the IndexingRunner, which
     deletes the document's existing segments before writing the new ones
     (core/indexing_runner.py:184).

Usage:
  py scripts/reindex_datasets.py                # dry run
  py scripts/reindex_datasets.py --apply        # all four datasets
  py scripts/reindex_datasets.py --apply --only sops
"""
import argparse
import json
import subprocess
import sys
import time

import requests

BASE = "http://localhost/v1"
CONSOLE = "http://localhost/console/api"

DATASETS = {
    "14f69bf6-8deb-4710-b5df-66e9edef6352": "manuals",
    "56c9585e-04cc-4e54-b171-7c6de6437b52": "sops",
    "680b6653-cefa-4e12-b633-7a91ce95aa13": "fault-cases",
    "1eda78d7-a791-4371-a3b4-55dcd73fc823": "parts",
}

SEPARATOR = "\\r\\n\\r\\n"
MAX_TOKENS = 200
CHUNK_OVERLAP = 0

PG = ["docker", "exec", "docker-db_postgres-1", "psql", "-U", "postgres", "-d", "dify", "-t", "-A", "-F", "|"]


def pg(sql):
    return subprocess.run(PG + ["-c", sql], capture_output=True, text=True, encoding="utf-8").stdout


def psql_exec(sql):
    out = subprocess.run(["docker", "exec", "docker-db_postgres-1", "psql", "-U", "postgres",
                          "-d", "dify", "-c", sql], capture_output=True, text=True, encoding="utf-8")
    return (out.stdout or out.stderr).strip()


def read_token(path):
    return subprocess.run(["docker", "exec", "docker-api-1", "cat", path],
                          capture_output=True, text=True, encoding="utf-8").stdout.strip()


CONSOLE_TOKEN = read_token("/tmp/admin_token.txt")
CSRF = read_token("/tmp/csrf_token.txt")
CH = {"Authorization": f"Bearer {CONSOLE_TOKEN}", "Content-Type": "application/json", "X-CSRF-Token": CSRF}
CC = {"csrf_token": CSRF, "__Host-csrf_token": CSRF,
      "access_token": CONSOLE_TOKEN, "__Host-access_token": CONSOLE_TOKEN}


def rules_json():
    return json.dumps({
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},
            {"id": "remove_urls_emails", "enabled": False},
        ],
        "segmentation": {"separator": SEPARATOR, "max_tokens": MAX_TOKENS, "chunk_overlap": CHUNK_OVERLAP},
        "parent_mode": None,
        "subchunk_segmentation": None,
    }, ensure_ascii=False)


def segments_of(dataset_id):
    rows = pg(f"SELECT id, document_id, position, length(content), content FROM document_segments "
              f"WHERE dataset_id='{dataset_id}' ORDER BY document_id, position;")
    out = []
    for line in rows.splitlines():
        if not line.strip():
            continue
        p = line.split("|")
        if len(p) >= 5:
            out.append({"id": p[0], "document_id": p[1], "position": p[2],
                        "len": int(p[3]), "content": p[4]})
    return out


def documents_of(dataset_id):
    rows = pg(f"SELECT id, name, indexing_status, coalesce(dataset_process_rule_id::text,'-') "
              f"FROM documents WHERE dataset_id='{dataset_id}' ORDER BY name;")
    out = []
    for line in rows.splitlines():
        if not line.strip():
            continue
        p = line.split("|")
        if len(p) >= 4:
            out.append({"id": p[0], "name": p[1], "status": p[2], "rule_id": p[3]})
    return out


def summarise(dataset_id):
    segs = segments_of(dataset_id)
    short = [s for s in segs if s["len"] < 60]
    pct = (100 * len(short) / len(segs)) if segs else 0
    print(f"  segments={len(segs):<4} under60chars={len(short):<4} ({pct:.0f}%)")
    return segs


def create_process_rule(dataset_id, account_id):
    """Insert a new custom DatasetProcessRule and return its id."""
    sql = (
        "INSERT INTO dataset_process_rules "
        "(id, dataset_id, mode, rules, created_by, created_at) VALUES "
        f"(uuid_generate_v4(), '{dataset_id}', 'custom', $j${json.dumps(json.loads(rules_json()), ensure_ascii=False)}$j$, "
        f"'{account_id}', now()) RETURNING id;"
    )
    out = pg(sql)
    for line in out.splitlines():
        line = line.strip()
        if len(line) == 36 and line.count("-") == 4:
            return line
    print("    ERROR creating process rule:", out[:300])
    return None


def point_documents_at_rule(dataset_id, rule_id):
    return psql_exec(f"UPDATE documents SET dataset_process_rule_id='{rule_id}' WHERE dataset_id='{dataset_id}';")


def reset_documents(dataset_id):
    return psql_exec(
        "UPDATE documents SET indexing_status='waiting', processing_started_at=NULL, "
        "parsing_completed_at=NULL, cleaning_completed_at=NULL, splitting_completed_at=NULL, "
        "completed_at=NULL, error=NULL, stopped_at=NULL, is_paused=false "
        f"WHERE dataset_id='{dataset_id}';"
    )


def retry_documents(dataset_id, doc_ids):
    r = requests.post(f"{CONSOLE}/datasets/{dataset_id}/retry", headers=CH, cookies=CC,
                      json={"document_ids": doc_ids}, timeout=180)
    return r.status_code, r.text[:200]


def wait_until_indexed(dataset_id, timeout=1200, interval=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        rows = pg(f"SELECT count(*) FILTER (WHERE indexing_status='completed'), "
                  f"count(*) FILTER (WHERE indexing_status='error'), count(*) "
                  f"FROM documents WHERE dataset_id='{dataset_id}';")
        try:
            done, errored, total = rows.strip().split("|")
        except ValueError:
            time.sleep(interval)
            continue
        print(f"    indexing completed={done} error={errored} total={total}")
        if done == total or int(done) + int(errored) == int(total):
            return int(errored)
        time.sleep(interval)
    return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    tenant_id = pg("SELECT tenant_id FROM datasets LIMIT 1;").strip()
    account_id = pg("SELECT id FROM accounts LIMIT 1;").strip()
    targets = {k: v for k, v in DATASETS.items() if not args.only or v == args.only}
    if not targets:
        print("no matching dataset")
        return 1
    print(f"tenant={tenant_id} account={account_id}")

    for ds_id, label in targets.items():
        print("=" * 74)
        print(f"{label}  {ds_id}")
        before = summarise(ds_id)
        docs = documents_of(ds_id)
        print(f"  documents={len(docs)} statuses={sorted({d['status'] for d in docs})}")

        if not args.apply:
            print(f"  WOULD apply separator={SEPARATOR!r} max_tokens={MAX_TOKENS} overlap={CHUNK_OVERLAP}")
            print(f"  WOULD re-index {len(docs)} documents (runner deletes the {len(before)} old segments)")
            continue

        rule_id = create_process_rule(ds_id, account_id)
        if not rule_id:
            continue
        print(f"  new process rule: {rule_id}")
        print("  " + point_documents_at_rule(ds_id, rule_id).splitlines()[0])
        print("  " + reset_documents(ds_id).splitlines()[0])

        code, body = retry_documents(ds_id, [d["id"] for d in docs])
        print(f"  retry {len(docs)} documents: HTTP {code} {body}")
        if code not in (200, 204):
            continue

        errored = wait_until_indexed(ds_id)
        print(f"  indexing finished, errors={errored}")
        after = summarise(ds_id)
        for s in after[:5]:
            print(f"    pos={s['position']} len={s['len']:<5} {s['content'][:85]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
