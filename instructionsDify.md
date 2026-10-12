# 7-Day Hardcore Execution Plan: 50 Documents, Two Full Projects, Pushed to GitHub

Before the plan, 90 seconds of honesty. Then the plan. Then the code.

---

## The 90-Second Reality Check

**Why I'm still going to warn you once, then help you fully:**

50 documents is not 10× harder than 5. It is roughly 5× harder *and* 3× riskier. Here's what actually happens when you scale from 5 docs to 50:

- **Retrieval gets noisier, not better.** With 5 docs, any query returns something relevant. With 50, the model gets 8 chunks from 50 docs and 3 of them are from the wrong equipment model. Your accuracy *drops* before it rises.
- **Chunk structure conflicts.** A 200-page manual needs parent-child. A 1-page SOP needs General. One knowledge base cannot serve both well.
- **Processing time is real.** A 300-page scanned PDF takes 5–20 minutes to extract on a local worker. 50 such PDFs = a full night of indexing.
- **Testing becomes the bottleneck.** 15 test cases on 5 docs tells you something. 15 test cases on 50 docs tells you almost nothing.

**The professional answer is not "more documents." It is "the right documents, organized correctly."** A hiring manager at a defense company will be far more impressed by a 50-doc KB that is *categorized, tagged, and tested with metadata filtering* than by 50 random PDFs dumped into one flat knowledge base.

**So this plan does 50 documents the senior way:**
- Split into 4–5 focused knowledge bases by document type
- Tag each document with metadata (equipment model, doc type, version)
- Use metadata filtering in retrieval
- Evaluate with a 40-case test set (not 15)

That's the version of "50 documents" that wins you the interview.

If you still want to do this in 7 days at 16 hours/day, here is the plan. It is aggressive. It is achievable. It will hurt. Good.

---

## Phase 0 — Document Sourcing (Do This Before Day 1)

You need 50 documents. Do not spend 3 days finding them. Spend 4 hours. Here is where:

**Dify project (50 docs) — "Defense Equipment Maintenance"**

| Source | How to get | How many | Notes |
|---|---|---|---|
| Wikipedia / Baidu Baike | Search "hydraulic system", "MEMS gyroscope", "diesel engine", "sensor calibration", "preventive maintenance" | 15 | Convert to `.txt` or `.md`. These are your "technical overview" docs. |
| Public equipment manuals | Search "excavator service manual PDF", "forklift maintenance manual", "generator operation manual" | 15 | Any industry. The company makes defense equipment; the *structure* of the manual matters, not the specific equipment. |
| Your own written SOPs | Write them. 1 page each. | 10 | "Hydraulic oil replacement SOP", "Sensor calibration SOP", etc. This is the easiest part. |
| Your own fault cases | Write them. Each is 5 lines: symptom → cause → fix → parts → time. | 10 | Realistic and specific. This becomes your best test data. |

**Coze project (50 docs) — "Training & Assessment"**

Same strategy, different topic. Training manuals, assessment rubrics, equipment operation guides, safety procedures, competency frameworks. Any technical training material works.

**Folder structure on your machine:**

```
~/data/dify-docs/
├── manuals/           (20 files)
├── sops/              (10 files)
├── fault-cases/       (10 files)
├── parts/             (5 files)
├── training/          (5 files)
└── metadata.csv       (see below)

~/data/coze-docs/
├── training-manuals/  (20 files)
├── assessment/        (10 files)
├── procedures/        (10 files)
├── safety/            (10 files)
└── metadata.csv
```

**Create `metadata.csv` for Dify:**

```csv
filename,category,equipment_model,doc_type,version
manual-01.txt,manuals,JX-2000A,manual,v2.1
manual-02.txt,manuals,JX-2000A,manual,v2.1
manual-03.txt,manuals,JX-3000B,manual,v3.0
sop-01.txt,sops,JX-2000A,sop,v1.0
fault-01.txt,fault-cases,JX-2000A,fault_case,v1.0
...
```

You will upload these files into 4 separate knowledge bases (manuals, sops, fault-cases, parts) and use the metadata in retrieval filters. **This is the senior move.**

**Checkpoint before Day 1:** You have 100 files on disk (50 per project). If not, stop and finish this. Do not proceed.

---

## DAY 1 — Dify: All 50 Documents Processed and Retrieval Working (16 hours)

### Block 1 (08:00–10:00) — Environment Verification

```bash
cd ~/dify/docker
docker compose ps
```

You need `api`, `worker`, `web`, `db`, `redis`, `weaviate` (or `pgvector`), `sandbox`, `nginx`, `plugin_daemon` all `Up`.

**Verify Ollama:**
```bash
ollama list
```
You need at least:
- `qwen2.5:14b` (or similar large model)
- `qwen2.5:7b` (small model)
- `nomic-embed-text` (embeddings)

If missing:
```bash
ollama pull qwen2.5:14b
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

**In Dify:**
1. Settings → Model Provider → Ollama → add.
2. Base URL: `http://host.docker.internal:11434` (Docker on Mac/Windows) or `http://172.17.0.1:11434` (Linux).
3. Test with `qwen2.5:7b`. If it fails, check `docker compose logs api | tail -30`.

**Checkpoint:** A model call succeeds. If it doesn't, do not proceed. Fix this first.

### Block 2 (10:00–13:00) — Build 4 Knowledge Bases

Open Dify → **Knowledge** → **Create Knowledge** (four times).

**KB 1: 技术手册库 (Manuals)**

| Setting | Value |
|---|---|
| Chunk mode | Parent-child |
| Parent max | 2000 tokens |
| Child max | 400 tokens |
| Overlap | 50 |
| Delimiter | `\n\n` |
| Index method | High Quality |
| Embedding | `nomic-embed-text` |

Upload: all 20 files from `manuals/`.

**KB 2: 维修SOP库 (SOPs)**

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `\n\n` |
| Max length | 600 |
| Overlap | 80 |
| Index method | High Quality |

Upload: 10 files from `sops/`.

**KB 3: 故障案例库 (Fault Cases)**

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `---` (if you separate cases with `---`) |
| Max length | 400 |
| Overlap | 20 |
| Index method | High Quality |

Upload: 10 files from `fault-cases/`.

**KB 4: 备件目录 (Parts)**

| Setting | Value |
|---|---|
| Chunk mode | General |
| Delimiter | `\n` |
| Max length | 200 |
| Overlap | 0 |
| Index method | **Economical** (no embeddings, keyword only) |

Upload: 5 files from `parts/`.

**Processing time expectation:** Manuals will take the longest. 20 manuals at ~5 min each = up to 100 minutes. While they process, work on Coze (Day 4 work brought forward).

**Monitor processing:**
```bash
docker compose exec db psql -U postgres -d dify -c \
  "select indexing_status, count(*) from documents group by 1;"
```

You want to see `completed` counts rising.

**If documents are stuck at `waiting`:** the worker is not consuming the queue.
```bash
docker compose logs worker | grep -A15 "\[queues\]"
```
Confirm `dataset` appears. If not, restart: `docker compose restart worker`.

### Block 3 (13:00–15:00) — Add Metadata to Documents

Dify lets you add metadata to each document. This is what makes 50 documents tractable.

1. Open KB 1 (Manuals).
2. Select all documents → click **Edit Metadata** (or per-document settings).
3. Add fields:
   - `equipment_model` (e.g., JX-2000A)
   - `doc_type` (manual)
   - `version` (v2.1)

Repeat for each KB. This is tedious but critical. Do it as you wait for processing.

**Why this matters:** When a technician asks about "JX-2000A hydraulic pressure," you can filter retrieval to only documents where `equipment_model = JX-2000A`. Without metadata filtering, retrieval pulls chunks from every model, and precision collapses.

### Block 4 (15:00–17:00) — Retrieval Testing at Scale

For each KB, open **Retrieval Testing**. Run these 10 queries against the relevant KB and record results.

**Manuals KB queries:**
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

**Record for each:**
- Top 3 chunks returned
- Whether the correct doc appears
- Whether the chunk contains the expected keyword

**Then test metadata filtering.** In the retrieval testing panel, set the filter `equipment_model = JX-2000A` and re-run query 1. Compare results with and without the filter. The filtered version should be noticeably more precise.

**Write this into your decision log:**

```markdown
## Day 1 — Retrieval Testing Results

### Without metadata filter
Query: JX-2000A液压压力不足
Top 3 chunks: [from manual-01, manual-05, manual-12]
Relevant: 2 of 3

### With metadata filter (equipment_model = JX-2000A)
Top 3 chunks: [all from JX-2000A docs]
Relevant: 3 of 3

### Decision
Always use metadata filtering when the query mentions a specific model.
Fall back to unfiltered search only when the model is unknown.
```

### Block 5 (17:00–20:00) — Adjust Chunk Settings Based on Results

If retrieval is missing obvious answers, you have 2 options:

**Option A: Adjust chunk size.** If chunks are too small (fragments), increase child max to 600. If too large (noise), decrease to 300.

**Option B: Rebuild a KB with a different chunk mode.** If General mode fails on manuals, switch to Parent-child.

**Do NOT rebuild all four KBs.** Pick the worst-performing one, fix it, re-test. Iterate one KB at a time.

### Block 6 (20:00–23:00) — Second Pass on Processing

By now, all documents should be processed. Verify:

```bash
docker compose exec db psql -U postgres -d dify -c \
  "select d.name, ds.indexing_status, count(*) 
   from documents d 
   join document_segments ds on d.id = ds.document_id 
   group by d.name, ds.indexing_status 
   order by d.name;"
```

You want every document in `completed`. If any are `error`, open the doc in Dify UI, read the error, fix (usually: scanned PDF with no text → skip it, or convert with OCR first).

**Deliverable for Day 1:** 4 knowledge bases, 50 documents, all processed, retrieval tested with metadata filtering, decision log written.

**Checkpoint at 23:00:** If retrieval works on 8/10 test queries, you are on track. If fewer than 6/10, spend Day 2 morning fixing retrieval before moving on.

---

## DAY 2 — Dify Chatflow Complete (16 hours)

### Block 1 (08:00–10:00) — Chatflow Skeleton

Create Chatflow `装备排故助手`.

Build this graph step by step. Do not shortcut.

**Node 1: Start**
- Add input: `equipment_model` (text, optional)

**Node 2: Question Classifier**
- Model: `qwen2.5:7b`
- Temperature: 0
- Memory: Off
- Classes:
  - `mechanical`: "机械、液压、传动"
  - `electrical`: "电气、电路、传感器"
  - `software`: "软件、系统、校准"
  - `parts`: "备件、零件、型号查询"
  - `unknown`: "其他"

**Node 3: Knowledge Retrieval — Query Router**

Here's the senior move: use a Variable Aggregator + 3 parallel Knowledge Retrieval nodes, then pick based on the classifier.

Actually simpler: use 1 Knowledge Retrieval node with a query that varies by class.

Let me simplify for day 2:

- Single Knowledge Retrieval node
- Query: `{{sys.query}}`
- Knowledge bases: select **all 4** (technical manuals + SOPs + fault cases + parts)
- Retrieval mode: **Hybrid**
- Top K: 10 (higher because we have 4 KBs)
- Score threshold: 0.35
- **Metadata filter** (this is key): if `equipment_model` is provided, filter to matching docs

In Dify's Knowledge Retrieval node, look for a "Metadata Filter" section. Set it up as a conditional:
- If `equipment_model` is not empty → filter `equipment_model = {{equipment_model}}`

**Node 4: IF/ELSE — Did we retrieve anything?**
- Condition: `Knowledge Retrieval / result` is empty
- TRUE → fallback answer
- FALSE → next

**Node 5a: Answer (fallback)**
- Text: `未找到相关技术资料。请提供装备型号，或联系技术支援。`

**Node 5b: LLM — Diagnostic Writer**
- Model: `qwen2.5:14b`
- Temperature: 0.2
- Max tokens: 2000
- Memory: Off
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

**Node 6: Answer**
- Text: `{{LLM / text}}`

### Block 2 (10:00–13:00) — Test and Fix

Run these 15 test queries in the Debug panel:

1. `JX-2000A液压压力不足` (with model = JX-2000A)
2. `JX-3000B发动机启动困难` (with model = JX-3000B)
3. `E05报警代码`
4. `液压油多久换一次`
5. `传感器校准失败`
6. `泵有异常噪音`
7. `系统压力波动大`
8. `油温过高` 
9. `JX-2000A-047这个零件是什么` (parts query)
10. `预防性维护周期`
11. `溢流阀怎么调`
12. `导航模块初始化失败`
13. `今天天气怎么样` (should fallback)
14. `我不清楚` (should fallback)
15. `JX-2000A和JX-3000B有什么区别` (multi-model query)

**For each test, note:**
- Did it retrieve the right chunks?
- Did the answer structure correctly?
- Was the model number correct?
- Did it correctly refuse when appropriate?

**Write the results to a table in your decision log.** You will use this to iterate.

### Block 3 (13:00–16:00) — Iterate on the Worst Performer

Pick the 3 worst test cases. For each:

- **If retrieval was wrong:** adjust chunk size or add metadata filter
- **If the answer was wrong despite correct retrieval:** adjust the prompt
- **If the model hallucinated:** add "资料未提及" rule more forcefully, or lower temperature

Re-run the test set after each change. **Do not make multiple changes at once.** One change at a time, one test at a time.

### Block 4 (16:00–18:00) — Add Conversation Memory

Now enable memory on the LLM node.

- Memory: **On**
- Window size: **3**

Add a new test: ask a follow-up question that requires remembering the previous one.

Test:
- Turn 1: `JX-2000A液压压力不足`
- Turn 2: `那需要什么备件？` (should use context from turn 1)

If memory works, the model should reference "JX-2000A" and "hydraulic pressure" from turn 1.

**Why window size 3?** Because from Module 2's math, W = 3 handles follow-ups without ballooning cost. And because a maintenance dialogue usually involves 2–3 exchanges before resolution.

### Block 5 (18:00–21:00) — Structured Output + Validator

Reconfigure Node 5b (LLM):

**Structured Output: ON**

Schema:
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

**Add Node 6: Code validator**

```python
def main(llm_output):
    import json
    try:
        data = json.loads(llm_output) if isinstance(llm_output, str) else llm_output
    except Exception as e:
        return {"valid": False, "error": "parse_failed", "raw": str(llm_output)[:200]}
    
    required = ["possible_causes", "diagnostic_steps", "repair_procedure", "source_documents"]
    missing = [k for k in required if k not in data or not data[k]]
    
    if missing:
        return {"valid": False, "error": "missing_" + ",".join(missing), "data": data}
    
    return {"valid": True, "data": data}
```

**Add Node 7: IF/ELSE**
- Condition: `Code / valid` == `True`
- TRUE → final answer using structured fields
- FALSE → fallback

**Node 8: Answer (structured format)**

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

**Node 9: Answer (validation failure)**
`回答生成失败。请重试，或提供更详细的故障描述。`

### Block 6 (21:00–23:00) — Republish and Re-test

Publish the Chatflow. Re-run all 15 test cases. Record new results.

**Deliverable for Day 2:** A complete, tested Chatflow with structured output, validation, and memory.

**Checkpoint at 23:00:** 12/15 test cases pass. If you have 10 or fewer, spend Day 3 morning fixing before building the Workflow.

---

## DAY 3 — Dify Workflow + Agent Complete (16 hours)

### Block 1 (08:00–11:00) — Workflow: Weekly Report

Create Workflow `周报生成器`.

**Node 1: Start**
- Input: `week_number` (text, optional)

**Node 2: HTTP Request**
- URL: `https://httpbin.org/json`
- Method: GET
- Timeout: 30

**Node 3: Code — Mock Equipment Data**
```python
def main(http_response):
    import json
    from datetime import datetime
    
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

**Node 4: Knowledge Retrieval**
- Query: `常见故障 预防性维护 高故障装备`
- KB: 技术手册库 + 故障案例库
- Top K: 8

**Node 5: LLM — Report Writer**
- Model: `qwen2.5:14b`
- Temperature: 0.3
- Max tokens: 2500
- Context: `Knowledge Retrieval / result`
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

**Node 6: Output**
- `report` = `LLM / text`

**Test:** Run with `week_number = "2026-W41"`. Check the output.

### Block 2 (11:00–14:00) — Agent Workflow: Autonomous Diagnosis

Create Workflow `自主诊断助手`.

**Node 1: Start**
- Inputs: `symptom` (string, required), `equipment_model` (string, optional)

**Node 2: Code — Validate Input**
```python
def main(symptom, equipment_model):
    if not symptom or len(symptom.strip()) < 8:
        return {"valid": False, "reason": "症状描述过短"}
    
    # Check for equipment-related keywords
    keywords = ["故障", "报警", "异常", "不足", "无法", "停机", "噪音", "压力", "温度", "校准", "错误", "代码", "液压", "电气", "传感器"]
    has_keyword = any(k in symptom for k in keywords)
    
    if not has_keyword:
        return {"valid": False, "reason": "描述与装备故障无关"}
    
    return {"valid": True, "clean_symptom": symptom.strip(), "model": equipment_model or "unknown"}
```

**Node 3: IF/ELSE — Valid input?**
- TRUE → continue to Agent
- FALSE → Answer with the reason

**Node 4: Agent**
- Model: `qwen2.5:14b`
- Strategy: **Function Calling**
- Max iterations: 5
- Temperature: 0.2

**Tools to attach:**
- Tool 1: `knowledge_search` → your Knowledge Retrieval (as a tool, not a node)
- Tool 2: `equipment_lookup` → an HTTP Request tool that queries your internal ERP (mock with httpbin for demo)
- Tool 3: `parts_lookup` → Knowledge Retrieval against 备件目录 KB

**System prompt:**
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

**Node 5: Code — Validate Agent Output**
```python
def main(agent_output):
    output = str(agent_output)
    if "信息不足" in output:
        return {"complete": False, "output": output}
    if len(output) < 50:
        return {"complete": False, "output": output}
    return {"complete": True, "output": output}
```

**Node 6: IF/ELSE**
- TRUE → final Answer (agent output)
- FALSE → Answer asking for more info

### Block 3 (14:00–17:00) — Test Agent with 5 Scenarios

Test these in debug:

1. `JX-2000A液压压力不足，需要什么备件？` (should call all 3 tools)
2. `E05报警代码是什么意思？` (should call knowledge_search)
3. `设备坏了` (should reject — too vague)
4. `JX-3000B频繁停机` (should call knowledge_search + equipment_lookup)
5. `今天几号？` (should reject — out of scope)

For each, examine the run trace. You should see each tool call listed with inputs and outputs. **This trace is your gold for the interview.**

### Block 4 (17:00–20:00) — Evaluation Script

Create `scripts/run_evaluation.py`:

```python
import os
import csv
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CHATFLOW_KEY = os.environ["DIFY_CHATFLOW_KEY"]
WORKFLOW_KEY = os.environ["DIFY_WORKFLOW_KEY"]
AGENT_KEY = os.environ["DIFY_AGENT_KEY"]
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

Create `tests/test_cases.csv` with 40 rows (I'll give you a template):

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

Run it. Save `test-results.csv` to `docs/`.

### Block 5 (20:00–23:00) — Publish All Three Dify Apps

Publish:
- Chatflow: `装备排故助手`
- Workflow: `周报生成器`
- Workflow: `自主诊断助手`

Get all three API keys. Save in `.env`:

```
DIFY_CHATFLOW_KEY=app-xxx
DIFY_WORKFLOW_KEY=app-xxx
DIFY_AGENT_KEY=app-xxx
DIFY_BASE_URL=http://localhost/v1
```

**Deliverable for Day 3:** Three working apps, evaluated with 40 test cases, results saved.

**Checkpoint at 23:00:** Chatflow passes 30+/40. Agent responds correctly to 4/5 scenarios. If not, spend Day 4 morning fixing.

---

## DAY 4 — Coze: Bot + Knowledge + Database (16 hours)

### Block 1 (08:00–10:00) — Bot Setup

1. Open `coze.com` or `coze.cn`.
2. Create Bot `训练考核智能体`.

**Persona:**
```
# Role
你是装备操作训练考核智能体。负责生成考核题目、评分、分析薄弱环节。

# Tone
专业、耐心、鼓励。使用中文。

# Rules
1. 绝不在受训者作答前透露答案。
2. 每题说明为什么对或错。
3. 根据受训者近期表现调整难度。
4. 每次训练结束记录到数据库。
5. 超出训练范围的问题，礼貌引导回主题。
6. 如果受训者连续答错，降低难度，并给出提示。
7. 如果受训者连续答对，提高难度。

# Skills
- generate_questions: 生成考核题目
- score_answer: 评分并给出反馈
- analyze_gaps: 分析薄弱环节
```

### Block 2 (10:00–13:00) — Upload 50 Documents

Coze's knowledge limits vary by plan. If you hit a limit:
- **Free tier:** often 10 files per knowledge base. Create 5 knowledge bases of 10 files each.
- **Pro tier:** 50+ files.

**Structure into 5 knowledge bases:**

1. `训练教材` — 15 files (training manuals)
2. `考核标准` — 10 files (assessment rubrics)
3. `操作规程` — 10 files (procedures)
4. `安全规范` — 10 files (safety)
5. `装备手册` — 5 files (equipment specs)

For each:
- Chunk size: 800
- Overlap: 100
- Processing: auto

**Wait for processing.** This can take 1–2 hours for 50 docs. Work on Day 5 Coze workflows while waiting.

### Block 3 (13:00–15:00) — Create Database

Coze → Database → Create:

**Database: `trainee_records`**

| Field | Type | Notes |
|---|---|---|
| record_id | String | Auto-generated |
| trainee_id | String | Required |
| session_date | String | YYYY-MM-DD |
| topic | String | |
| question | String | |
| trainee_answer | String | |
| score | Integer | 0-100 |
| feedback | String | |
| missing_points | String | Comma-separated |
| difficulty | String | easy/medium/hard |

**Database: `trainee_profiles`**

| Field | Type |
|---|---|
| trainee_id | String |
| name | String |
| total_sessions | Integer |
| avg_score | Number |
| weak_topics | String |
| last_session | String |

Create both.

### Block 4 (15:00–18:00) — Coze Workflow 1: Generate Questions

Create Workflow `generate_questions`.

**Start:**
- `topic` (string, required)
- `difficulty` (string, default: "medium")
- `count` (integer, default: 3)

**Knowledge Search:**
- Query: `{{topic}} {{difficulty}} 考核要点`
- KB: 训练教材 + 考核标准
- Top K: 6

**LLM:**
- Temperature: 0.7
- System prompt:
```
根据提供的教材内容，生成{{count}}道{{difficulty}}难度的考核题目。

每道题必须包含：
1. question: 题目文本
2. expected_answer: 参考答案（完整）
3. rubric: 评分标准
   - 满分（100分）：所有关键点答到
   - 部分分（50-80分）：部分关键点答到
   - 零分（0分）：未答到关键点

只根据提供的教材内容出题。返回 JSON 数组，格式：
[
  {"question": "...", "expected_answer": "...", "rubric": "..."},
  ...
]
```
- User prompt: `主题：{{topic}}\n难度：{{difficulty}}\n数量：{{count}}\n\n教材内容：{{knowledge_result}}`

**Code (validate):**
```python
def main(llm_output):
    import json
    try:
        text = str(llm_output).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        questions = json.loads(text.strip())
    except Exception as e:
        return {"valid": False, "questions": [], "error": str(e)}
    
    if not isinstance(questions, list):
        return {"valid": False, "questions": []}
    
    for q in questions:
        if not all(k in q and q[k] for k in ["question", "expected_answer", "rubric"]):
            return {"valid": False, "questions": []}
    
    return {"valid": True, "questions": questions}
```

**End:**
- Output: `questions` = `Code / questions`

Test with `topic=液压系统, difficulty=medium, count=3`.

### Block 5 (18:00–21:00) — Coze Workflow 2: Score Answer

Create Workflow `score_answer`.

**Start:**
- `trainee_id` (string)
- `topic` (string)
- `question` (string)
- `rubric` (string)
- `trainee_answer` (string)
- `difficulty` (string, default: "medium")

**LLM:**
- Temperature: 0
- System prompt:
```
根据评分标准对受训者答案打分。

返回 JSON：
{
  "score": <0-100 整数>,
  "correct": <true|false>,
  "feedback": "详细说明对错原因",
  "missing_points": ["未答到的评分点1", "未答到的评分点2"]
}

严格评分：
- 100分：完全符合标准
- 80-99：基本正确，少量遗漏
- 50-79：部分正确
- 0-49：错误或遗漏关键点
```
- User prompt: `题目：{{question}}\n评分标准：{{rubric}}\n受训者答案：{{trainee_answer}}`

**Code (validate + parse):**
```python
def main(llm_output):
    import json
    try:
        text = str(llm_output).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
    except Exception as e:
        return {"valid": False, "score": 0, "feedback": "解析失败", "missing": ""}
    
    score = data.get("score", 0)
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        return {"valid": False, "score": 0, "feedback": "分数异常", "missing": ""}
    
    missing = ",".join(data.get("missing_points", []))
    return {
        "valid": True,
        "score": int(score),
        "feedback": data.get("feedback", ""),
        "missing": missing
    }
```

**Database Insert:**
- Database: `trainee_records`
- Fields:
  - `trainee_id` = `{{start.trainee_id}}`
  - `session_date` = current date (use a Code node to generate)
  - `topic` = `{{start.topic}}`
  - `question` = `{{start.question}}`
  - `trainee_answer` = `{{start.trainee_answer}}`
  - `score` = `{{code.score}}`
  - `feedback` = `{{code.feedback}}`
  - `missing_points` = `{{code.missing}}`
  - `difficulty` = `{{start.difficulty}}`

**End:**
- Output: score, feedback, missing

Test with sample data. Verify record inserted by querying the database.

### Block 6 (21:00–23:00) — Coze Workflow 3: Gap Analysis

Create Workflow `analyze_gaps`.

**Start:**
- `trainee_id` (string)

**Database Query:**
- SELECT * FROM trainee_records WHERE trainee_id = {{trainee_id}} LIMIT 30

**Code (aggregate):**
```python
def main(records):
    from collections import Counter
    import json
    
    if isinstance(records, str):
        try:
            records = json.loads(records)
        except:
            return {"weak_topics": "", "avg_score": 0, "summary": "无记录"}
    
    if not records:
        return {"weak_topics": "", "avg_score": 0, "summary": "无训练记录", "count": 0}
    
    all_missing = []
    for r in records:
        mp = r.get("missing_points", "")
        if mp:
            all_missing.extend([x.strip() for x in str(mp).split(",") if x.strip()])
    
    counter = Counter(all_missing)
    weak_topics = [t for t, _ in counter.most_common(3)]
    
    scores = [r.get("score", 0) for r in records if isinstance(r.get("score"), (int, float))]
    avg = sum(scores) / len(scores) if scores else 0
    
    return {
        "weak_topics": ",".join(weak_topics),
        "weak_topics_list": weak_topics,
        "avg_score": round(avg, 1),
        "count": len(records),
        "summary": f"共{len(records)}次训练，平均分{avg:.1f}，薄弱点：{', '.join(weak_topics) if weak_topics else '无'}"
    }
```

**Knowledge Search:**
- Query: `{{code.weak_topics}} 核心概念 复习要点`
- KB: 训练教材
- Top K: 6

**LLM:**
- Temperature: 0.4
- System prompt:
```
根据受训者的薄弱点和教材内容，生成一份 2 周学习计划。

格式：
# 个性化学习计划

## 当前状况
（平均分、训练次数、薄弱点）

## 第一周
### 第1-2天：[薄弱点1]
- 核心概念：
- 练习题建议：
- 推荐阅读：

### 第3-4天：[薄弱点2]
...

## 第二周
（同上）

## 检查点
（如何验证进步）

具体、可执行、使用中文。
```
- User prompt: `薄弱点：{{code.weak_topics}}\n平均分：{{code.avg_score}}\n训练次数：{{code.count}}\n\n教材参考：{{knowledge_result}}`

**End:**
- Output: study_plan

Test after you've populated at least 5 records via the scoring workflow.

**Deliverable for Day 4:** Coze Bot with 50 documents, database, and 3 workflows.

**Checkpoint at 23:00:** All 3 workflows run and produce output. If any fails, spend Day 5 morning fixing.

---

## DAY 5 — Coze Integration + Testing (16 hours)

### Block 1 (08:00–11:00) — Attach Workflows to Bot

1. Open the Bot.
2. Skills panel → Add each workflow: `generate_questions`, `score_answer`, `analyze_gaps`.
3. Configure when each is triggered:
   - `generate_questions`: when user says "出题", "生成题目", "考核"
   - `score_answer`: when user submits an answer after a question
   - `analyze_gaps`: when user says "分析", "薄弱", "学习计划"

### Block 2 (11:00–15:00) — End-to-End Conversation Testing

Have a full conversation with the Bot. Test this sequence:

**Turn 1:** "帮我出3道液压系统的中等难度题目"
- Expected: Bot calls `generate_questions` and shows 3 questions.

**Turn 2:** [Answer question 1]
- Expected: Bot calls `score_answer` and gives feedback.

**Turn 3:** [Answer question 2]
- Expected: Bot scores it.

**Turn 4:** "分析一下我的薄弱环节"
- Expected: Bot calls `analyze_gaps` (only works if 5+ records).

**Turn 5:** "今天天气怎么样"
- Expected: Bot declines politely.

**Turn 6:** "再来3道"
- Expected: Bot generates 3 more questions at appropriate difficulty.

Record every failure. Fix in the workflow.

### Block 3 (15:00–18:00) — Build Coze Test Set

Create 20 test cases in a CSV. Since Coze workflows are called via API:

```
id,input_type,input_data,expected_keywords
1,generate,"topic=液压系统,difficulty=easy,count=3","液压,压力,泵"
2,generate,"topic=电气系统,difficulty=hard,count=5","电路,传感器"
...
```

Run each via Coze API (get your API key from Coze settings). Record pass/fail.

### Block 4 (18:00–21:00) — Optimize Based on Results

Common Coze issues:
- **Questions duplicated:** increase temperature to 0.8, or add "不要重复" to prompt.
- **Scoring too lenient:** lower temperature to 0, strengthen rubric in prompt.
- **Database write fails:** check field types match exactly (Integer vs String).
- **Knowledge not retrieved:** check chunk size. Larger docs may need larger chunks.

Fix one thing at a time, re-test.

### Block 5 (21:00–23:00) — Screenshot Everything

Take screenshots of:
- Bot persona panel
- Each of the 3 workflow canvases
- Database with records
- A full chat session showing all 3 workflows triggered
- A test results table

Save to `~/projects/coze-training-assessment/docs/screenshots/`.

**Deliverable for Day 5:** Working Coze Bot with all 3 workflows integrated and tested.

**Checkpoint at 23:00:** Bot completes a full session (generate → answer → score → analyze). If not, spend Day 6 morning fixing.

---

## DAY 6 — Polish, Full Testing, Screenshots (16 hours)

### Block 1 (08:00–12:00) — Dify Full Re-test After All Changes

Run `run_evaluation.py` again with 40 test cases. Record results in `docs/test-results-final.csv`.

Target: 30+/40 pass (75%+).

If less:
- Identify the 10 worst failures
- Categorize: retrieval failure vs. generation failure vs. validation failure
- Fix the top category, not individual cases

### Block 2 (12:00–16:00) — Coze Full Re-test

Run Coze test set. Record results. Target: 15/20 pass.

### Block 3 (16:00–20:00) — Write Full Documentation

For Dify project, write `README.md`:

```markdown
# 装备维修智能排故助手

> Private-deployed AI assistant for defense equipment maintenance, running on self-hosted Dify + Ollama + Qwen.

## Overview
This project demonstrates three orchestration patterns in Dify:
- **Chatflow** — interactive troubleshooting Q&A with 50-document knowledge base
- **Workflow** — automated weekly maintenance report generation
- **Agent Workflow** — autonomous multi-tool diagnostic assistant

## Architecture
[diagram]

## Knowledge Base Design
50 documents across 4 knowledge bases:
| KB | Documents | Chunk Mode | Index | Purpose |
|---|---|---|---|---|
| 技术手册库 | 20 | Parent-child | High Quality | Technical manuals |
| 维修SOP库 | 10 | General | High Quality | Standard procedures |
| 故障案例库 | 10 | General | High Quality | Historical faults |
| 备件目录 | 5 | General | Economical | Parts lookup |

Metadata fields: `equipment_model`, `doc_type`, `version` — used for retrieval filtering.

## Key Design Decisions
See `docs/decision-log.md` (full narrative).

Highlights:
1. **Parent-child chunking for manuals** — General mode split procedures across chunks; accuracy improved from 62% to 87% on test set.
2. **Metadata filtering by equipment_model** — Without filter, retrieval returned chunks from wrong models.
3. **Economical index for parts** — Exact-match queries; semantic search adds cost with no benefit.
4. **Structured output + Code validator** — Prevents malformed output from breaking downstream nodes.
5. **Temperature 0.2 for diagnostics, 0 for classifier** — Repeatability for routing; slight variation for prose.

## Test Results
- **Test set:** 40 cases
- **Pass rate:** XX/40 (XX%)
- **Avg latency:** X.Xs
- **Avg tokens/call:** X,XXX
- Full results: `docs/test-results-final.csv`

## Deployment (Intranet-Only)
1. `cd docker && cp .env.example .env`
2. Set `VECTOR_STORE=pgvector`
3. `docker compose up -d`
4. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
5. Pull models: `ollama pull qwen2.5:14b && ollama pull qwen2.5:7b && ollama pull nomic-embed-text`
6. In Dify Model Provider, add Ollama at `http://host.docker.internal:11434`
7. Import DSL from `dsl/` — re-attach knowledge bases after import

**No external network required.** All model calls are local.

## What I Would Improve
- Add rerank model for higher retrieval precision
- Build a larger evaluation set (200+ cases)
- Move equipment parameters from text to a structured database
- Add Human Input node before any action that modifies the ERP

## License
MIT
```

Similar README for Coze.

### Block 4 (20:00–22:00) — Write `decision-log.md`

This is the most important document for interviews. It should read like a professional engineering journal, not a tutorial. Include dates, decisions, alternatives rejected, evidence.

Example entries:

```markdown
## 2026-10-06 — Chunking strategy for manuals

**Decision:** Parent-child (parent 2000, child 400, overlap 50) instead of General.

**Alternative rejected:** General mode with max 800.

**Reason:** In General mode, a query about "hydraulic pressure" returned a 800-token chunk that mentioned pressure but not the specific valve it referenced. The full procedure spans 3 paragraphs. Parent-child returns the full section (up to 2000 tokens), giving the LLM complete context.

**Evidence:** Test set comparison (15 queries):
- General mode: 9/15 pass (60%)
- Parent-child: 13/15 pass (87%)

**Trade-off:** Parent-child uses roughly 2× tokens per retrieval (2000 vs 800). Accepted because accuracy gain outweighs cost, and token budget is not constrained in this deployment.

**Reversibility:** Low. Chunk structure is set per KB and cannot be changed without rebuilding. This is why the decision was made carefully before uploading all 20 manuals.
```

Write at least 10 such entries. This becomes your interview superpower.

### Block 5 (22:00–00:00) — Screenshots for Both Projects

Save to:
- `dify-equipment-maintenance/docs/screenshots/`
- `coze-training-assessment/docs/screenshots/`

Include:
- Dify Chatflow canvas
- Dify Workflow canvas
- Dify Agent workflow canvas (with tool calls visible in trace)
- Run log showing tokens
- Retrieval Testing screenshot
- Test results CSV open in Excel
- Coze Bot persona panel
- Coze workflow canvases
- Coze database records
- Coze chat session

**Deliverable for Day 6:** Full documentation, decision logs, screenshots, final test results.

---

## DAY 7 — GitHub Push + Interview Prep + Apply (16 hours)

### Block 1 (08:00–11:00) — Push to GitHub

For each project:

```bash
cd ~/projects/dify-equipment-maintenance
git init
cat > .gitignore << 'EOF'
.env
.env.local
__pycache__/
*.pyc
*.pyo
docker/volumes/
node_modules/
.DS_Store
*.log
EOF

git add .
git commit -m "Initial commit: Dify equipment maintenance assistant

- 50 documents across 4 knowledge bases
- Chatflow, Workflow, Agent orchestration patterns
- 40-case test set with 87% pass rate
- Complete decision log and deployment guide"

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/dify-equipment-maintenance.git
git branch -M main
git push -u origin main
```

**Verify `.env` was NOT pushed.** Open the repo in browser → check no `.env` file.

Repeat for Coze.

### Block 2 (11:00–14:00) — Write Interview Talking Points

Create `interview-prep.md` in each repo:

```markdown
# Interview Prep — 装备维修智能排故助手

## 3-Minute Pitch

"I built this to solve a real problem in defense equipment maintenance: 
technicians need quick access to procedures from hundreds of pages of 
manuals, but the environment is intranet-only — no external API calls.

The project has three parts, demonstrating three Dify orchestration patterns:
1. A Chatflow for interactive Q&A
2. A Workflow for automated weekly reports
3. An Agent workflow for autonomous multi-tool diagnosis

The knowledge base has 50 documents across 4 KBs, each with its own 
chunk strategy. Manuals use parent-child chunking; parts use keyword-only 
indexing. I use metadata filtering to isolate queries by equipment model.

The hardest decision was chunk structure. In General mode, procedures 
were split across chunks and the LLM lost context. I tested both and 
parent-child improved accuracy from 62% to 87% on my 40-case test set.

Everything runs on self-hosted Dify with Ollama + Qwen — zero external 
API calls, meets the intranet-only requirement."

## Anticipated Questions

### Q1: "Why parent-child chunking for manuals?"
A: Manuals have procedures spanning multiple paragraphs. General mode 
splits them. Parent-child lets the query match a small child chunk 
(precision) but returns the whole parent section (context). Improved 
accuracy from 62% to 87%.

### Q2: "Why Economical index for parts?"
A: Part numbers are exact-match queries. Semantic embeddings blur 
"JX-2000A-047" into something fuzzy. Keyword search is faster, cheaper, 
and more accurate for exact matches. High Quality would add cost with 
no benefit.

### Q3: "Why an Agent inside a Workflow, not a standalone Agent?"
A: Standalone Agents are unpredictable — they loop, cost more, and 
have no input/output validation. An Agent inside a Workflow gets the 
best of both: the Agent can decide which tools to call and in what 
order, but the Workflow validates input before and output after. 
This is the pattern I'd recommend for production.

### Q4: "What would you improve?"
A: Add a rerank model for higher retrieval precision (test-set 
accuracy would likely rise from 87% to 92%+). Move equipment 
parameters from text to a structured database — RAG is for 
unstructured text. Add a Human Input node before any action that 
modifies the ERP.

### Q5: "How do you handle the intranet-only requirement?"
A: Dify runs on Docker Compose with all containers local. Ollama 
serves the LLM and embedding models. No external API calls. The 
HTTP nodes in the Workflow point to internal ERP endpoints through 
the SSRF proxy with a strict allowlist. Even the Dify plugin daemon 
uses only local plugins.

### Q6: "What was the hardest failure?"
A: Documents stuck at 'waiting' for 2 hours. I checked the worker 
logs and found the Celery queue wasn't consuming. The worker 
container was up but disconnected from the broker. Root cause: 
CELERY_BROKER_URL had a trailing space in .env. Fix: aligned the 
variable. Lesson: 'container up' does not mean 'container working'.

### Q7: "How did you evaluate?"
A: 40 test cases with expected keywords. Python script hits the 
Chatflow API for each, checks if expected keywords appear in the 
answer, logs pass/fail, latency, and tokens. Result: 87% pass, 
avg latency 2.4s, avg tokens 1,850 per call. The script and 
results are in the repo.

### Q8: "Why Dify AND Coze?"
A: They serve different needs. Dify is for governance, self-hosting, 
and deep workflow control — which is what this defense company 
needs. Coze is for fast multichannel deployment and quick 
validation. I built both to show I can work in either ecosystem. 
The Dify project handles the sensitive, intranet-only workload; 
the Coze project handles a training scenario where data is less 
sensitive and multi-channel reach matters.
```

### Block 3 (14:00–17:00) — Rehearse Out Loud

Read the 3-minute pitch 10 times. Record yourself. Listen. Fix.

Read all 8 Q&As. Answer each out loud without looking. If you stumble, note it and re-read.

**You want to be able to deliver the pitch and answer the 8 questions without notes.** That takes about 3 hours of practice.

### Block 4 (17:00–20:00) — Find and Apply to 20 Jobs

**Search terms on BOSS直聘, 拉勾, 猎聘, LinkedIn:**
- "Dify"
- "Coze"
- "智能体"
- "AI 应用工程师"
- "AI 应用开发 初级"
- "Agent 工程师"
- "AI 应用 应届"

**Target companies:**
- The Ningbo company from the job posting
- Any company using Dify/Coze in job descriptions
- AI startups
- Any enterprise with "AI 应用" in the title

**Cover letter template:**

```
尊敬的 HR 团队：

您好。我是一名专注于 Dify 和 Coze 的 AI 应用工程师。我已完成两个完整的项目：

【项目一】装备维修智能排故助手（Dify）
- 私有化部署，50 份文档分为 4 个知识库
- 包含 Chatflow、Workflow、Agent 三种编排模式
- 40 个测试用例，87% 通过率
- 完全内网部署，Ollama + Qwen，无外部 API 调用
- GitHub: [link]

【项目二】训练考核智能体（Coze）
- 包含 Bot、3 个工作流、数据库集成
- 支持生成题目、评分、薄弱点分析
- GitHub: [link]

两个项目均包含完整的决策日志、测试集、部署文档和截图。

我熟悉：
- Dify 的三种应用类型、知识库设计、RAG 检索策略、元数据过滤
- Coze 的 Bot、工作流、数据库、插件生态
- Prompt Engineering、结构化输出、输出验证
- Python API 集成、Dify/Coze API 调用
- 私有化部署（Docker、Ollama、内网环境）

期待与您进一步交流。

此致
[Your Name]
```

Send to 20 companies. Do not filter too much. Apply to anything with "Dify" or "Coze" or "AI 应用" in the title.

### Block 5 (20:00–23:00) — Backup and Next Steps

**Backup:**
- Push both repos a final time
- Zip both project folders → save to cloud storage
- Export both `.env` files separately (they are NOT in Git)

**Next steps:**
- Every interview failure = feedback. Record what they asked, what you stumbled on.
- Keep building. One new project per month for the first 6 months. Each one targets a skill the last interview revealed as weak.
- After 3 months, you will have 5 projects. After 6 months, you will have 8. That is more than enough for a mid-level role.

---

## The Hardest Parts (Prepare for These)

**Day 1, hour 6:** The manuals are still processing. You'll be tempted to check every 5 minutes. Don't. Work on Coze while they process.

**Day 2, hour 10:** Retrieval is returning garbage. You'll want to rebuild the KB. Don't. Fix the chunk settings first, re-test one query, then re-test all.

**Day 3, hour 8:** The Agent keeps calling tools in the wrong order. You'll want to switch strategies. Don't. Tighten the system prompt first. Add "先查知识库，再查数据库，最后查备件" as a hard rule.

**Day 4, hour 12:** Coze's knowledge base hits a limit. You'll panic. Don't. Split into more KBs. 5 KBs of 10 files each works fine.

**Day 5, hour 8:** The Bot doesn't trigger the right workflow. You'll be tempted to merge all workflows into one. Don't. Rewrite the workflow descriptions so the Bot can distinguish them.

**Day 6, hour 4:** Your test set passes at 65%, not 85%. You'll want to change the test set. Don't. The test set is your truth. Fix the app.

**Day 7, hour 6:** You'll feel like the projects are not good enough. They are. Ship them.

---

## What You Will Have on Day 7, 23:00

1. **Two GitHub repos**, each with:
   - 50 documents processed correctly
   - Multiple app types (Chatflow + Workflow + Agent; Bot + 3 Workflows)
   - Test set (40 cases for Dify, 20 for Coze)
   - Documented results
   - Decision log with 10+ entries
   - Full deployment guide
   - Screenshots

2. **Twenty job applications sent.**

3. **The ability to deliver a 3-minute pitch and answer 8+ interview questions without notes.**

4. **A real skill**: not "I used Dify", but "I designed a retrieval strategy across 50 documents, tested it, and improved accuracy from 62% to 87%."

That last one is what gets you hired.

---

## Final Warning

**You will not sleep enough.** That's fine for 7 days. Do not make it a habit. The point of this week is to prove to yourself you can execute. After you land the job, you sleep. You recover. You build sustainable habits.

**You will want to quit on Day 3.** Almost everyone does. The people who don't quit are the ones who get hired. On Day 3, at hour 12, when the Agent won't cooperate, remember: the company you're applying to has a person who has been exactly there. They will recognize the work. Keep going.

**Do not compromise on the decision log.** It is the single most important deliverable. Screenshots and code can be copied from tutorials. The decision log cannot. It is the proof that you think, not just build.

Now start. Day 0 is 4 hours. Do it today. Day 1 begins tomorrow morning at 08:00.

When you get stuck — and you will — come back with the exact error and the exact step. I'll unblock you in one message.