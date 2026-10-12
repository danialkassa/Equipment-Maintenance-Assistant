# Dify Project Plan: Equipment Maintenance Assistant

Build a privately deployed Dify application with 50 documents and three apps (Chatflow, Workflow, Agent), tested with a 40-case evaluation set and pushed to GitHub.

- **Day 0 (4h):** Prepare 50 documents
- **Day 1:** Knowledge bases and retrieval
- **Day 2:** Chatflow
- **Day 3:** Workflow + Agent + evaluation
- **Day 4:** Final testing, documentation, GitHub

---

## Phase 0 — Prepare 50 Documents (4 hours, before Day 1)

### Sources

| Source | How to get | Count |
|---|---|---|
| Technical overviews | Search Wikipedia / Baidu Baike for "hydraulic system", "MEMS gyroscope", "diesel engine", "sensor calibration", "preventive maintenance"; save as `.txt` or `.md` | 10 |
| Public equipment manuals | Search "excavator service manual PDF", "forklift maintenance manual", "generator operation manual" | 10 |
| Self-written SOPs | 1 page each, e.g. "Hydraulic oil replacement SOP", "Sensor calibration SOP" | 10 |
| Self-written fault cases | 5 lines each: symptom → cause → fix → parts → time | 10 |
| Parts catalogs | Part-number lists copied/derived from the manuals | 10 |

The manual *structure* is what matters, not the specific equipment brand.

### Folder structure

```
dify-equipment-maintenance/data/dify-docs/
├── manuals/           (20 files: 10 overviews + 10 manuals)
├── sops/              (10 files)
├── fault-cases/       (10 files)
├── parts/             (10 files)
└── metadata.csv
```

### `metadata.csv`

```csv
filename,category,equipment_model,doc_type,version
manual-01.txt,manuals,JX-2000A,manual,v2.1
manual-02.txt,manuals,JX-2000A,manual,v2.1
manual-03.txt,manuals,JX-3000B,manual,v3.0
sop-01.txt,sops,JX-2000A,sop,v1.0
fault-01.txt,fault-cases,JX-2000A,fault_case,v1.0
parts-01.txt,parts,JX-2000A,parts,v1.0
...
```

**Checkpoint:** 50 files on disk and `metadata.csv` completed. Do not start Day 1 without this.

---

## DAY 1 — Knowledge Bases and Retrieval

### Block 1 — Verify environment

```bash
cd ~/dify/docker
docker compose ps
```

Required containers all `Up`: `api`, `worker`, `web`, `db`, `redis`, `weaviate` (or `pgvector`), `sandbox`, `nginx`, `plugin_daemon`.

Verify Ollama models:

```bash
ollama list
```

Required: `qwen2.5:14b`, `qwen2.5:7b`, `nomic-embed-text`. Pull if missing.

In Dify: **Settings → Model Provider → Ollama → Add**
- Base URL: `http://host.docker.internal:11434` (Docker Desktop) or `http://172.17.0.1:11434` (Linux)
- Test with `qwen2.5:7b`

**Checkpoint:** A model test call succeeds. Fix this before anything else.

### Block 2 — Create 4 knowledge bases

Dify → **Knowledge → Create Knowledge** (four times).

**KB 1: 技术手册库 (Manuals)** — upload all 20 files from `manuals/`

| Setting | Value |
|---|---|
| Chunk mode | Parent-child |
| Parent max | 2000 tokens |
| Child max | 400 tokens |
| Overlap | 50 |
| Delimiter | `\n\n` |
| Index method | High Quality |
| Embedding | `nomic-embed-text` |

**KB 2: 维修SOP库 (SOPs)** — upload 10 files from `sops/`

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `\n\n` |
| Max length | 600 |
| Overlap | 80 |
| Index method | High Quality |

**KB 3: 故障案例库 (Fault Cases)** — upload 10 files from `fault-cases/`

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `---` |
| Max length | 400 |
| Overlap | 20 |
| Index method | High Quality |

**KB 4: 备件目录 (Parts)** — upload 10 files from `parts/`

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `\n` |
| Max length | 200 |
| Overlap | 0 |
| Index method | Economical (keyword only) |

Manuals take longest to index (~5 min each). Monitor:

```bash
docker compose exec db psql -U postgres -d dify -c \
  "select indexing_status, count(*) from documents group by 1;"
```

If documents are stuck at `waiting`, check the worker queue:

```bash
docker compose logs worker | grep -A15 "\[queues\]"
```

Confirm the `dataset` queue appears; if not, `docker compose restart worker`.

### Block 3 — Add metadata

For each KB: select documents → **Edit Metadata**, add fields:
- `equipment_model` (e.g. JX-2000A)
- `doc_type` (manual / sop / fault_case / parts)
- `version` (e.g. v2.1)

Metadata lets retrieval filter to one equipment model. Without it, queries return chunks from every model and precision drops.

### Block 4 — Retrieval testing

In each KB, open **Retrieval Testing** and run the queries below. For each, record: top 3 chunks, whether the correct document appears, whether the chunk contains the expected keyword.

Manuals KB queries:

1. `JX-2000A液压压力不足`
2. `JX-3000B发动机启动困难`
3. `液压油更换步骤`
4. `传感器校准方法`
5. `E05报警代码含义`
6. `预防性维护周期`
7. `溢流阀调节方法`
8. `油温过高原因`
9. `泵异常噪音`
10. `系统压力波动`

Then test the metadata filter: set `equipment_model = JX-2000A`, re-run query 1, and compare against the unfiltered result. Record both in `docs/decision-log.md`:

```markdown
## Day 1 — Retrieval Testing Results

### Without metadata filter
Query: JX-2000A液压压力不足
Top 3 chunks: [manual-01, manual-05, manual-12]
Relevant: 2 of 3

### With metadata filter (equipment_model = JX-2000A)
Top 3 chunks: [all from JX-2000A docs]
Relevant: 3 of 3

### Decision
Always use metadata filtering when the query names a specific model.
Fall back to unfiltered search only when the model is unknown.
```

### Block 5 — Tune chunk settings (only the worst-performing KB)

- Fragments / missing context → increase child chunk size (e.g. 400 → 600)
- Noisy / oversized chunks → decrease it (e.g. 400 → 300)
- General mode failing on long manuals → rebuild that one KB as Parent-child

Fix one KB at a time and re-test. Do not rebuild all four.

### Block 6 — Verify all documents completed

```bash
docker compose exec db psql -U postgres -d dify -c \
  "select d.name, ds.indexing_status, count(*)
   from documents d
   join document_segments ds on d.id = ds.document_id
   group by d.name, ds.indexing_status
   order by d.name;"
```

Every document must be `completed`. For `error` documents, read the error in the UI (usually a scanned PDF with no text layer — OCR it first or replace it).

**Day 1 deliverable:** 4 knowledge bases, 50 documents indexed, retrieval tested with and without metadata filtering, decision log started.

**Checkpoint:** 8/10 retrieval queries return the right document. If below 6/10, fix retrieval before Day 2.

---

## DAY 2 — Chatflow: 装备排故助手

### Block 1 — Build the chatflow

Create a **Chatflow** named `装备排故助手`.

**Node 1 — Start**
- Input variable: `equipment_model` (text, optional)

**Node 2 — Knowledge Retrieval**
- Query: `{{sys.query}}`
- Knowledge bases: all 4
- Retrieval mode: Hybrid
- Top K: 10
- Score threshold: 0.35
- Metadata filter: if `equipment_model` is not empty, filter `equipment_model = {{equipment_model}}`

**Node 3 — IF/ELSE (retrieval empty?)**
- Condition: `Knowledge Retrieval / result` is empty
- TRUE → fallback answer: `未找到相关技术资料。请提供装备型号，或联系技术支援。`
- FALSE → continue

**Node 4 — LLM (Diagnostic Writer)**
- Model: `qwen2.5:14b`
- Temperature: 0.2
- Max tokens: 2000
- Memory: Off (enabled later in Block 4)
- Context: `Knowledge Retrieval / result`
- System prompt:

```
你是装备维修技术专家。根据提供的技术资料回答用户问题。

回答结构（使用 Markdown）：
## 可能原因
（列出2-5条，每条一句话）

## 诊断步骤
（编号，每步一个具体动作）

## 维修流程
（编号，每步一个具体操作）

## 安全警告
（如有，否则写"无"）

## 参考文档
（列出使用的文档名称）

规则：
- 只使用提供的资料，绝不编造
- 每个诊断步骤标注来源文档
- 资料中没有的内容，明确说"资料未提及"
- 中文回答，专业简洁
```

- User prompt: `装备型号：{{equipment_model}}\n\n故障描述：{{sys.query}}`

**Node 5 — Answer:** `{{LLM / text}}`

### Block 2 — Test 15 queries

Run in the Debug panel:

1. `JX-2000A液压压力不足` (model = JX-2000A)
2. `JX-3000B发动机启动困难` (model = JX-3000B)
3. `E05报警代码`
4. `液压油多久换一次`
5. `传感器校准失败`
6. `泵有异常噪音`
7. `系统压力波动大`
8. `油温过高`
9. `JX-2000A-047这个零件是什么`
10. `预防性维护周期`
11. `溢流阀怎么调`
12. `导航模块初始化失败`
13. `今天天气怎么样` (must fallback)
14. `我不清楚` (must fallback)
15. `JX-2000A和JX-3000B有什么区别` (multi-model)

For each, record: correct chunks retrieved? answer structure correct? model number correct? correctly refused when appropriate? Write results as a table in the decision log.

### Block 3 — Fix the 3 worst cases

- Wrong retrieval → adjust chunk size or metadata filter
- Right retrieval but wrong answer → adjust the prompt
- Hallucination → strengthen the "资料未提及" rule, lower temperature

One change at a time; re-run after each change.

### Block 4 — Enable memory

On the LLM node: Memory **On**, window size **3**.

Verify with a multi-turn test:
- Turn 1: `JX-2000A液压压力不足`
- Turn 2: `那需要什么备件？`

Turn 2 must reference JX-2000A and hydraulic pressure from turn 1.

### Block 5 — Structured output + validation

Reconfigure the LLM node: **Structured Output: ON**, schema:

```json
{
  "type": "object",
  "properties": {
    "possible_causes": {"type": "array", "items": {"type": "string"}},
    "diagnostic_steps": {"type": "array", "items": {"type": "string"}},
    "repair_procedure": {"type": "array", "items": {"type": "string"}},
    "safety_warnings": {"type": "array", "items": {"type": "string"}},
    "source_documents": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["possible_causes", "diagnostic_steps", "repair_procedure", "source_documents"]
}
```

Add a **Code** node (validator):

```python
def main(llm_output):
    import json
    try:
        data = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
    except Exception:
        return {"valid": False, "error": "parse_failed", "raw": str(llm_output)[:200]}

    required = ["possible_causes", "diagnostic_steps", "repair_procedure", "source_documents"]
    missing = [k for k in required if not data.get(k)]

    if missing:
        return {"valid": False, "error": "missing_" + ",".join(missing), "data": data}

    return {"valid": True, "data": data}
```

Add **IF/ELSE** on `Code / valid == True`:
- TRUE → Answer node rendering structured fields:

```
## 可能原因
{{Code / data.possible_causes}}

## 诊断步骤
{{Code / data.diagnostic_steps}}

## 维修流程
{{Code / data.repair_procedure}}

## 安全警告
{{Code / data.safety_warnings}}

## 参考文档
{{Code / data.source_documents}}
```

- FALSE → Answer: `回答生成失败。请重试，或提供更详细的故障描述。`

### Block 6 — Publish and re-test

Publish the chatflow and re-run all 15 cases.

**Day 2 deliverable:** Published chatflow with hybrid retrieval, metadata filtering, memory, structured output, and validation.

**Checkpoint:** 12/15 cases pass. If ≤10, fix before Day 3.

---

## DAY 3 — Workflow, Agent, Evaluation

### Block 1 — Workflow: 周报生成器 (Weekly Report)

Create a **Workflow**.

**Node 1 — Start:** input `week_number` (text, optional)

**Node 2 — HTTP Request** (mock ERP endpoint)
- URL: `https://httpbin.org/json`, Method: GET, Timeout: 30

**Node 3 — Code (mock equipment data):**

```python
def main(http_response):
    import json

    # Mock data - replace with real ERP query in production
    equipment = [
        {"id": "JX-2000A-001", "model": "JX-2000A", "status": "operational", "last_maintenance": "2026-09-15", "fault_count_30d": 0},
        {"id": "JX-2000A-002", "model": "JX-2000A", "status": "maintenance_due", "last_maintenance": "2026-08-01", "fault_count_30d": 2},
        {"id": "JX-2000A-005", "model": "JX-2000A", "status": "operational", "last_maintenance": "2026-09-20", "fault_count_30d": 1},
        {"id": "JX-3000B-007", "model": "JX-3000B", "status": "fault", "last_maintenance": "2026-09-20", "fault_count_30d": 5},
        {"id": "JX-3000B-008", "model": "JX-3000B", "status": "operational", "last_maintenance": "2026-09-25", "fault_count_30d": 1},
        {"id": "NX-100-012", "model": "NX-100", "status": "operational", "last_maintenance": "2026-09-01", "fault_count_30d": 1},
        {"id": "NX-100-013", "model": "NX-100", "status": "maintenance_due", "last_maintenance": "2026-07-15", "fault_count_30d": 0},
    ]

    overdue = [e for e in equipment if e["status"] == "maintenance_due"]
    high_fault = [e for e in equipment if e["fault_count_30d"] >= 3]
    faulty = [e for e in equipment if e["status"] == "fault"]

    summary = {
        "total": len(equipment),
        "operational": len([e for e in equipment if e["status"] == "operational"]),
        "overdue_count": len(overdue),
        "overdue_ids": [e["id"] for e in overdue],
        "high_fault_count": len(high_fault),
        "high_fault_ids": [e["id"] for e in high_fault],
        "faulty_ids": [e["id"] for e in faulty],
        "equipment": equipment
    }

    return {"summary_json": json.dumps(summary, ensure_ascii=False)}
```

**Node 4 — Knowledge Retrieval**
- Query: `常见故障 预防性维护 高故障装备`
- KBs: 技术手册库 + 故障案例库
- Top K: 8

**Node 5 — LLM (Report Writer)**
- Model: `qwen2.5:14b`, Temperature: 0.3, Max tokens: 2500
- System prompt:

```
你是装备维护管理助理。根据提供的数据撰写周报。

周报结构：
# 装备维护周报 — {{week_number}}

## 一、总体概况
- 装备总数：X
- 正常运行：X
- 需维护：X
- 故障：X

## 二、需关注装备
（列出ID、型号、原因）

## 三、高故障装备分析
（结合技术资料，分析可能原因）

## 四、本周建议行动
（具体、可执行、编号）

## 五、技术参考
（引用的技术资料）

使用中文，专业简洁，数据准确。
```

- User prompt: `数据：{{Code / summary_json}}\n\n技术参考：{{Knowledge Retrieval / result}}`

**Node 6 — End:** `report` = `{{LLM / text}}`

Test with `week_number = "2026-W41"`.

### Block 2 — Workflow: 自主诊断助手 (Autonomous Diagnosis)

Create a second **Workflow**.

**Node 1 — Start:** `symptom` (string, required), `equipment_model` (string, optional)

**Node 2 — Code (input validation):**

```python
def main(symptom, equipment_model):
    if not symptom or len(symptom.strip()) < 8:
        return {"valid": False, "reason": "症状描述过短"}

    keywords = ["故障", "报警", "异常", "不足", "无法", "停机", "噪音", "压力", "温度", "校准", "错误", "代码", "液压", "电气", "传感器"]
    if not any(k in symptom for k in keywords):
        return {"valid": False, "reason": "描述与装备故障无关"}

    return {"valid": True, "clean_symptom": symptom.strip(), "model": equipment_model or "unknown"}
```

**Node 3 — IF/ELSE:** valid → continue; invalid → Answer with the reason.

**Node 4 — Agent**
- Model: `qwen2.5:14b`, Strategy: Function Calling, Max iterations: 5, Temperature: 0.2
- Tools:
  - `knowledge_search` — Knowledge Retrieval over manuals + fault cases
  - `equipment_lookup` — HTTP Request tool (mock ERP with httpbin)
  - `parts_lookup` — Knowledge Retrieval over 备件目录 KB
- System prompt:

```
你是自主诊断助手。根据用户提供的故障描述，自主决定调用哪些工具来诊断。

可用工具：
- knowledge_search: 查询维修技术手册和故障案例
- equipment_lookup: 查询装备状态数据库
- parts_lookup: 查询备件目录

诊断流程：
1. 先用 knowledge_search 查找相似故障
2. 如果知道装备型号，用 equipment_lookup 查询其当前状态
3. 如果需要更换部件，用 parts_lookup 查询库存
4. 综合所有工具结果给出诊断

规则：
- 最多调用5次工具
- 5次后仍无法确定，输出"信息不足"并列出还需要什么数据
- 每个结论都引用工具返回的证据
- 使用中文回答
```

**Node 5 — Code (output validation):**

```python
def main(agent_output):
    output = str(agent_output)
    if "信息不足" in output or len(output) < 50:
        return {"complete": False, "output": output}
    return {"complete": True, "output": output}
```

**Node 6 — IF/ELSE:** complete → final Answer with agent output; incomplete → Answer asking for more information.

### Block 3 — Test the agent with 5 scenarios

1. `JX-2000A液压压力不足，需要什么备件？` (all 3 tools)
2. `E05报警代码是什么意思？` (knowledge_search only)
3. `设备坏了` (rejected — too vague)
4. `JX-3000B频繁停机` (knowledge_search + equipment_lookup)
5. `今天几号？` (rejected — out of scope)

Open the run trace for each and verify tool calls, inputs, and outputs.

### Block 4 — Evaluation script and test set

Create `scripts/run_evaluation.py`:

```python
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
    body = {"inputs": {"equipment_model": model}, "query": question, "user": "eval", "response_mode": "blocking"}
    start = time.time()
    try:
        r = requests.post(url, headers=headers, json=body, timeout=90)
        elapsed = time.time() - start
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "latency": elapsed}
        data = r.json()
        usage = data.get("metadata", {}).get("usage", {})
        return {
            "answer": data.get("answer", ""),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency": round(elapsed, 2)
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
        passed = hits >= max(1, len(expected) // 2)
        result.update({
            "id": case["id"],
            "question": case["question"],
            "expected_keywords": case["expected_keywords"],
            "hits": hits,
            "total_expected": len(expected),
            "passed": passed
        })
        results.append(result)
        time.sleep(0.5)

    with open("../docs/test-results.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    passed = sum(1 for r in results if r.get("passed"))
    avg_lat = sum(r["latency"] for r in results) / len(results)
    total_tok = sum(r.get("total_tokens", 0) for r in results)
    print(f"\nPassed: {passed}/{len(results)} ({100*passed//len(results)}%)")
    print(f"Avg latency: {avg_lat:.2f}s")
    print(f"Total tokens: {total_tok}")

if __name__ == "__main__":
    main()
```

Create `tests/test_cases.csv` with 40 rows:

```csv
id,question,equipment_model,expected_keywords
1,JX-2000A液压压力不足,JX-2000A,溢流阀,泵,压力
2,JX-3000B发动机启动困难,JX-3000B,启动,燃油,点火
3,E05报警代码,,E05,超载,传感器
4,液压油多久换一次,,液压油,更换,周期
5,传感器校准失败,JX-2000A,校准,零偏,IMU
6,泵有异常噪音,JX-3000A,泵,噪音,轴承
7,系统压力波动大,,压力,波动,溢流
8,油温过高,JX-2000A,油温,散热,冷却
9,JX-2000A-047是什么零件,,JX-2000A-047,备件
10,预防性维护周期,,维护,周期,检查
11,溢流阀怎么调节,,溢流阀,调节,压力
12,导航模块初始化失败,NX-100,导航,初始化,IMU
13,今天天气,,,
14,我不清楚,,,
15,JX-2000A和JX-3000B的区别,,JX-2000A,JX-3000B,区别
16,JX-2000A更换液压油步骤,JX-2000A,液压油,排空,加注
17,发动机水温过高,JX-3000B,水温,冷却,节温器
18,系统报错E12,,E12,错误
19,振动传感器读数异常,JX-2000A,振动,传感器
20,备用电源无法启动,,电源,启动,电池
21,如何检测液压油质,,液压油,检测,污染
22,JX-3000B油泵异响,JX-3000B,油泵,异响
23,控制面板黑屏,,面板,屏幕,电源
24,JX-2000A保养周期,JX-2000A,保养,周期,保养项
25,液压系统漏油,,液压,漏油,密封
26,发动机冒黑烟,JX-3000B,黑烟,燃油,燃烧
27,压力传感器校准,,压力传感器,校准
28,JX-2000A-012备件库存,,JX-2000A-012,库存
29,系统无法连接网络,,网络,连接
30,液压泵不工作,JX-2000A,液压泵,工作
31,温度传感器报警,,温度传感器,报警
32,发动机机油压力低,JX-3000B,机油,压力
33,如何更换空气滤芯,,空气滤芯,更换
34,液压油颜色变黑,JX-2000A,液压油,颜色
35,系统响应缓慢,,系统,响应,缓慢
36,备用电池更换周期,,备用电池,更换
37,JX-2000A噪音异常,JX-2000A,噪音,异常
38,发动机启动后熄火,JX-3000B,启动,熄火
39,液压缸动作缓慢,JX-2000A,液压缸,动作
40,遥控器无响应,,遥控器,响应
```

Note: rows 13–14 are negative cases — a correct fallback answer counts as a pass in your manual review.

Run the script; results save to `docs/test-results.csv`.

### Block 5 — Publish all three apps

Publish `装备排故助手`, `周报生成器`, `自主诊断助手`. Save API keys to `.env`:

```
DIFY_CHATFLOW_KEY=app-xxx
DIFY_WORKFLOW_KEY=app-xxx
DIFY_AGENT_KEY=app-xxx
DIFY_BASE_URL=http://localhost/v1
```

**Day 3 deliverable:** Three working apps, 40-case evaluation run with results saved.

**Checkpoint:** Chatflow 30+/40 pass; agent correct on 4/5 scenarios.

---

## DAY 4 — Final Testing, Documentation, GitHub

### Block 1 — Final evaluation run

Re-run `run_evaluation.py`, save to `docs/test-results-final.csv`. Target: 30+/40 (75%+).

If below target:
1. List the 10 worst failures
2. Categorize each as retrieval failure, generation failure, or validation failure
3. Fix the largest category, not individual cases
4. Re-run

### Block 2 — Write `README.md`

```markdown
# 装备维修智能排故助手

> Privately deployed AI assistant for equipment maintenance, running on self-hosted Dify + Ollama + Qwen.

## Overview
Three orchestration patterns in Dify:
- **Chatflow** — interactive troubleshooting Q&A over 50 documents
- **Workflow** — automated weekly maintenance report
- **Agent Workflow** — autonomous multi-tool diagnosis

## Knowledge Base Design
| KB | Documents | Chunk Mode | Index | Purpose |
|---|---|---|---|---|
| 技术手册库 | 20 | Parent-child | High Quality | Technical manuals |
| 维修SOP库 | 10 | General | High Quality | Standard procedures |
| 故障案例库 | 10 | General | High Quality | Historical faults |
| 备件目录 | 10 | General | Economical | Parts lookup |

Metadata fields: `equipment_model`, `doc_type`, `version` — used in retrieval filters.

## Key Design Decisions
1. Parent-child chunking for manuals — long procedures stay in one parent chunk.
2. Metadata filtering by equipment_model — prevents cross-model chunk noise.
3. Economical index for parts — part numbers are exact-match; semantic search adds cost with no benefit.
4. Structured output + Code validator — malformed LLM output cannot break downstream nodes.
5. Temperature 0.2 for diagnostics — repeatable, low-variation answers.

## Test Results
- Test set: 40 cases
- Pass rate: XX/40 (XX%)
- Avg latency: X.Xs
- Avg tokens/call: X,XXX
- Full results: docs/test-results-final.csv

## Deployment (intranet-only)
1. `cd docker && cp .env.example .env`
2. Set `VECTOR_STORE=pgvector`
3. `docker compose up -d`
4. Install Ollama and pull `qwen2.5:14b`, `qwen2.5:7b`, `nomic-embed-text`
5. In Dify, add Ollama at `http://host.docker.internal:11434`
6. Import DSL from `dsl/` and re-attach the knowledge bases

No external network required — all model calls are local.

## What I Would Improve
- Add a rerank model for higher retrieval precision
- Expand the evaluation set to 200+ cases
- Move equipment parameters from text to a structured database
- Add a Human Input node before any ERP-modifying action
```

### Block 3 — Write `docs/decision-log.md`

Write at least 10 entries. Each entry: date, decision, alternative rejected, reason, evidence, trade-off. Example:

```markdown
## 2026-10-06 — Chunking strategy for manuals

**Decision:** Parent-child (parent 2000, child 400, overlap 50) instead of General.

**Alternative rejected:** General mode, max 800 tokens.

**Reason:** General mode split multi-paragraph procedures across chunks; the LLM
received a fragment mentioning pressure but not the valve adjustment it depended on.

**Evidence (15-query comparison):**
- General mode: 9/15 pass (60%)
- Parent-child: 13/15 pass (87%)

**Trade-off:** ~2x tokens per retrieval. Accepted — accuracy gain outweighs cost,
and the deployment is local with no token budget constraint.

**Reversibility:** Low — chunk mode requires rebuilding the KB. Decide before upload.
```

Suggested decision topics: chunk mode per KB, chunk sizes, hybrid vs vector retrieval, Top K and threshold values, metadata filtering, Economical vs High Quality index, temperature choices, memory window size, structured output schema, agent iteration limit, agent-in-workflow vs standalone agent.

### Block 4 — Screenshots

Save to `docs/screenshots/`:
- All three app canvases (chatflow, weekly report workflow, agent workflow)
- Agent run trace with tool calls visible
- Retrieval Testing panel
- Knowledge base settings for all 4 KBs
- `test-results-final.csv` open in a spreadsheet
- A run log showing token usage

### Block 5 — Push to GitHub

```bash
cd /c/Users/Healer/Documents/trae_projects/dify-equipment-maintenance
git init
```

Create `.gitignore`:

```
.env
.env.local
__pycache__/
*.pyc
*.pyo
docker/volumes/
node_modules/
.DS_Store
*.log
```

```bash
git add .
git commit -m "Initial commit: Dify equipment maintenance assistant

- 50 documents across 4 knowledge bases
- Chatflow, Workflow, Agent orchestration patterns
- 40-case test set with documented results
- Decision log and deployment guide"

git remote add origin https://github.com/YOUR_USERNAME/dify-equipment-maintenance.git
git branch -M main
git push -u origin main
```

Verify in the browser that `.env` was not pushed.

---

## Final Deliverables Checklist

- [ ] 50 documents indexed across 4 knowledge bases, all `completed`
- [ ] Metadata on every document; filter tested
- [ ] Chatflow published: hybrid retrieval, metadata filter, memory, structured output, validator
- [ ] Weekly report workflow published
- [ ] Agent workflow published, tool-call traces verified
- [ ] `tests/test_cases.csv` (40 cases) + `scripts/run_evaluation.py`
- [ ] `docs/test-results-final.csv` — 30+/40 pass
- [ ] `docs/decision-log.md` — 10+ dated entries
- [ ] `README.md` with architecture, decisions, results, deployment
- [ ] Screenshots
- [ ] GitHub repo pushed, `.env` confirmed excluded
