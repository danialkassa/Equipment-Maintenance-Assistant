# Beginner Guide: Configure the Dify Equipment Maintenance Assistant

This guide assumes you have never used Dify before. The documents are prepared and Dify is already running. Follow the **minimum working path first**: one knowledge retrieval node, one DeepSeek text node, and one Answer node. Do not build the advanced routing until the simple Chatflow works.

Every step tells you **where to click** and **what to type**. Button names can differ slightly between Dify versions — if a button is not exactly where described, look for the same word elsewhere on the same panel.

**Required first:**

- Four knowledge bases using the prepared documents
- One simple **Chatflow** that answers equipment-fault questions

**Add later, after the Chatflow works:**

- A **Workflow** that writes a weekly maintenance report
- An **Agent Workflow** that diagnoses faults by calling tools

---

# PART 1 — Day 1: Build Knowledge Bases

## 1.1 Open Dify and log in

1. Open your browser, go to `http://localhost`.
2. First time only: create an admin email/password and sign in.
3. You land on the **Studio** page (list of apps).

## 1.2 Configure Knowledge Base 1 — Manuals (20 files)

1. Click **Knowledge** in the top menu.
2. Click **Create Knowledge**. This creates a Dify knowledge base, not the source documents; the 20 source files are already prepared.
3. Click **Upload file** (or drag-and-drop). The project includes five consolidated manual files specifically for Dify's upload limit.
4. In the file picker, paste this path into the filename box and press Enter:

```
C:\Users\Healer\Documents\trae_projects\dify-equipment-maintenance\data\dify-docs\manuals-upload
```

1. Press **Ctrl+A** to select all five files → click **Open**.
2. Confirm that all five consolidated files are listed, then click **Next**.
3. Name the knowledge base: `技术手册库 (Manuals)`.
4. Set the chunking and indexing options:
   | Field on screen           | What to choose/type                                           |
   | ------------------------- | ------------------------------------------------------------- |
   | Chunking mode cards       | **Parent-child**                                              |
   | Parent-chunk for Context  | `2000`                                                        |
   | Child-chunk for Retrieval | `400`                                                         |
   | Delimiter                 | leave `\n\n`; if a **Chunk overlap** field is shown, set `50` |
   | Index Method              | **High Quality**                                              |
   | Embedding model           | **nomic-embed-text**                                          |
5. Click **Save & Process** (bottom of page).
6. You return to the Knowledge page; documents show **queued / processing / completed**. Large files take several minutes. Continue with the next KB while it processes.

The five uploaded files contain all 20 original manuals. The original files remain in the `manuals` folder for reference; upload only the files from `manuals-upload`.

**If you already uploaded five original manuals:** delete those five documents from the Manuals knowledge base first, then upload the five consolidated files. Do not keep both sets, or retrieval may return duplicate content. If Dify does not allow deletion while the files are processing, wait until processing finishes and then delete them.

## 1.3 Configure Knowledge Base 2 — SOPs (10 files)

Repeat the same steps with these differences:

1. **Create Knowledge** → upload all files from `C:\Users\Healer\Documents\trae_projects\dify-equipment-maintenance\data\dify-docs\sops`.
2. Name: `维修SOP库 (SOPs)`.
3. Settings:
   | Field                | Value            |
   | -------------------- | ---------------- |
   | Chunking mode cards  | **General**      |
   | Maximum chunk length | `600`            |
   | Chunk overlap        | `80`             |
   | Delimiter            | `\n\n`           |
   | Index Method         | **High Quality** |
   | Embedding model      | nomic-embed-text |
4. **Save & Process**.

## 1.4 Configure Knowledge Base 3 — Fault Cases (10 files)

1. Upload all files from `C:\Users\Healer\Documents\trae_projects\dify-equipment-maintenance\data\dify-docs\fault-cases`.
2. Name: `故障案例库 (Fault Cases)`.
3. Settings: **General** card, **Maximum chunk length** `400`, **Chunk overlap** `20`, **Delimiter** `---`, **Index Method: High Quality**, **Embedding model** nomic-embed-text.
4. **Save & Process**.

## 1.5 Configure Knowledge Base 4 — Parts (10 files)

1. Upload all files from `C:\Users\Healer\Documents\trae_projects\dify-equipment-maintenance\data\dify-docs\parts`.
2. Name: `备件目录 (Parts)`.
3. Settings: **General** card, **Maximum chunk length** `200`, **Chunk overlap** `0`, **Delimiter** `\n`.
4. **Index Method: Economical** (keyword only — no embeddings). Part numbers are exact matches.
5. **Save & Process**.

## 1.6 Check processing finished

1. Click **Knowledge** → click into each knowledge base.
2. Every document must show a green **completed** state (no `waiting`, no red `error`).
3. If a document is red: click it, read the error. For these plain-text files errors are unlikely; if one appears, re-upload that file.

## Optional advanced setup: add metadata to the documents

Metadata lets the app filter answers by equipment model. Add **three text fields** to every document: `equipment_model`, `doc_type`, `version`.

**Do this one knowledge base at a time.**

1. Click **Knowledge** → open `技术手册库 (Manuals)`.
2. Click the checkbox at the top of the document list to **select all** (or tick individual rows).
3. Click the **Edit Metadata** button above the list.
4. Click **Add Metadata** → choose the **String** type → name it `doc_type` → value `manual` → **Save**.
5. Select all again → click **Add Metadata** and add `version`. Set the value for each consolidated file:
   - `manuals-jx-2000a-part-1.txt` and `manuals-jx-2000a-part-2.txt` → `v2.1`
   - `manuals-jx-3000b.txt` → `v3.0`
   - `manuals-nx-100.txt` → `v1.0`
   - `manuals-all-models.txt` → `mixed` (the original files inside it have different versions)
6. Click **Add Metadata** and add `equipment_model` to each consolidated file:
   | Model value | Select this uploaded file                                    |
   | ----------- | ------------------------------------------------------------ |
   | `JX-2000A`  | `manuals-jx-2000a-part-1.txt`, `manuals-jx-2000a-part-2.txt` |
   | `JX-3000B`  | `manuals-jx-3000b.txt`                                       |
   | `NX-100`    | `manuals-nx-100.txt`                                         |
   | `ALL`       | `manuals-all-models.txt`                                     |

Repeat for the other KBs. `doc_type` is the same for the whole KB: SOPs = `sop`, fault cases = `fault_case`, parts = `parts`.

## Optional advanced setup: test retrieval

1. Open the Manuals KB → click the **Retrieval Testing** button (top-right).
2. In the test box type: `JX-2000A液压压力不足` → press Enter.
3. Look at the returned chunks: they should mention 溢流阀 / 压力 and come from JX-2000A documents.
4. Type these one at a time and check each returns sensible chunks:
   - `JX-3000B发动机启动困难`
   - `液压油更换步骤`
   - `传感器校准方法`
   - `E05报警代码含义`
   - `溢流阀调节方法`
   - `油温过高原因`
5. If the Retrieval Testing panel has a **metadata filter** section, set `equipment_model = JX-2000A`, re-run query 1, and confirm the chunks all come from JX-2000A documents.
6. Open `docs/decision-log.md`, add the result, and save:

```markdown
# Decision Log

## Day 1 — Retrieval test: JX-2000A液压压力不足
Without filter: returned chunks from ___ (how many relevant of 3).
With filter equipment_model=JX-2000A: ___ of 3 relevant.
Decision: always filter by model when the question names a model.
```

**Basic Day 1 checkpoint:** all four knowledge bases show their documents as **completed**.

---

# PART 2 — Day 2: Build the Chatflow

The chatflow answers maintenance questions, filters documents by equipment model, and outputs a structured diagnostic answer.

## 2.1 Create the app

1. Click **Studio** (top menu) → **Create from Blank**.
2. Choose the **Chatflow** tile.
3. Name: `Equipment Maintenance Assistant` → click **Create**.
4. The visual canvas opens with a **Start** node.

## 2.2 Add the user input variable

For the minimum working Chatflow, do not add a custom equipment-model variable. Dify already provides the user's message as `sys.query`, and that is enough for the first version.

Leave the **Start** node unchanged and continue to section 2.3. You add the `equipment_model` variable later, and only if you build the optional advanced route below — that route's first step tells you how.

## 2.3 Minimum working Chatflow

Build this straight line only:

`Start → Maintenance Retrieval → Maintenance Diagnosis LLM → Final Maintenance Answer`

1. Click the **`+`** connector below the **Start** node.
2. Choose **Knowledge Retrieval** and name it `Maintenance Retrieval`.
3. Configure the retrieval node:
   - **Query:** choose **sys.query** with the `{x}` variable picker.
   - **Knowledge:** add all four knowledge bases and confirm.
   - **Retrieval mode:** choose **Hybrid Search**. If unavailable, choose **Vector Search + Full-text Search**.
   - **Top K:** `10`.
   - **Score threshold:** `0.35`.
   - Do not add metadata filters in this first version.
4. From the output of `Maintenance Retrieval`, click **`+`** → choose **LLM**. Name it `Maintenance Diagnosis LLM`.
5. Configure the LLM:
   - **Model:** select your configured **DeepSeek text model**. Do not select an image model.
   - **Temperature:** `0.2`.
   - **Context:** add `Maintenance Retrieval / result`.
6. In the LLM **SYSTEM** prompt, paste:

```
你是装备维修技术专家。只根据提供的技术资料回答用户问题。

请使用以下结构：
## 可能原因
## 诊断步骤
## 维修流程
## 安全警告
## 参考文档

规则：
- 只使用提供的资料，不要编造。
- 资料中没有的内容，明确说“资料未提及”。
- 使用中文，回答简洁、具体。
```

1. From the output of `Maintenance Diagnosis LLM`, click **`+`** → choose **Answer**.
2. Name the answer node `Final Maintenance Answer` and insert **Maintenance Diagnosis LLM → text/body** with the variable picker.

At this point the basic Chatflow is complete. Test it in section 2.4 before adding anything else.

## 2.4 Test the minimum Chatflow

1. Click **Debug & Preview**.
2. Ask: `JX-2000A液压压力不足`.
3. Confirm that the answer contains causes, diagnostic steps, a repair procedure, safety information, and source documents.
4. Test these questions one at a time:
   - `JX-3000B发动机启动困难`
   - `E05报警代码是什么意思`
   - `传感器校准失败`
   - `JX-2000A-047这个零件是什么`
5. If the answer is poor, first adjust only the retrieval settings or the prompt. Do not add more nodes yet.


**Stop here until the simple Chatflow works. Skip the following advanced sections for now. They are optional enhancements, not required for the first working version.**

After this test, scroll down to **2.5 Publish the minimum Chatflow**. Ignore every heading that starts with **Optional**.

## Optional advanced route: filter by equipment model

These optional sections rebuild the simple straight line from 2.3 into a routed flow. Do not keep both sets of retrieval/LLM nodes on the same path.

**Before this route works, two things must exist on the canvas — add them first:**

1. Open the **Start** node → under **Input Field**, click the **+** button → name `equipment_model`, type **Short Text**, **not required** (an empty value means the question has no model).
2. Click the **`+`** connector below the **Start** node → choose **IF/ELSE**. Name it `Model Filter Check`. Create this condition: **Start → equipment_model** + comparison **is empty**.

The IF/ELSE node has two paths. Only one path runs for each user question:

- **IF path:** the user did not enter an equipment model, so search all four knowledge bases without a model filter.
- **ELSE path:** the user entered an equipment model, so search all four knowledge bases with an `equipment_model` filter.

### IF path: search without a model filter

1. Start at the **IF** output of the IF/ELSE node.
2. Click the line's **`+`** button → choose **Knowledge Retrieval**.
3. Name the node `Retrieval - All Models`.
4. Configure this node:
   - **Query:** choose **sys.query** with the `{x}` variable picker.
   - **Knowledge:** add all four knowledge bases, then confirm.
   - **Retrieval mode:** **Hybrid Search**. If Hybrid Search is unavailable, choose **Vector Search + Full-text Search**.
   - **Top K:** `10`.
   - **Score threshold:** `0.35`.
   - **Metadata filtering:** leave it empty. Do not add a model condition on this path.

### ELSE path: search the selected model

1. Start at the **ELSE** output of the same IF/ELSE node.
2. Click the line's **`+`** button → choose **Knowledge Retrieval**.
3. Name the node `Retrieval - Selected Model`.
4. Configure the same Query, Knowledge, Retrieval mode, Top K, and Score threshold as the first node.
5. Add one metadata condition:
   - **Field:** `equipment_model`
   - **Operator:** **equals / is**
   - **Value:** choose **Start → equipment_model** with the variable picker.

Do not connect either retrieval node directly to the LLM. Both retrieval nodes must first connect to the same Variable Aggregator.

## Optional advanced route: combine the two branch outputs

1. Click the output of `Retrieval - All Models` → **`+`** → choose **Variable Aggregator**.
2. Name it `Combined Retrieval Context`.
3. In the Aggregator, click **Add Variable** and select:
   - `Retrieval - All Models / result`
   - `Retrieval - Selected Model / result`
4. Connect the output of `Retrieval - Selected Model` to this same Aggregator. The Aggregator accepts whichever retrieval branch ran; the other variable is empty.

## Optional advanced route: handle an empty retrieval result

This step adds a decision after the retrieval result. It sends the conversation to a fallback message when no document was found, or to the LLM when documents were found.

1. Find the node named `Combined Retrieval Context` on the canvas.
2. Click the **`+`** connector on the right side of that node.
3. Choose **IF/ELSE**. The new IF/ELSE node must be directly after `Combined Retrieval Context`.
4. In the IF/ELSE settings, create this condition:
   - Click **Select variable** (or the `{x}` icon).
   - Select **Combined Retrieval Context** → **output**.
   - Select the comparison **is empty**. If your Dify version does not show that option, choose **contains no data**.
5. Confirm that the node displays two outputs:
   - **IF / True:** the retrieval output is empty.
   - **ELSE / False:** the retrieval output contains documents.
6. On the **IF / True** connector, click **`+`** and choose **Answer**. Name this answer node `No Results Fallback`. Paste this message:

```
未找到相关技术资料。请提供装备型号，或联系技术支援。
(No relevant technical document found. Please provide the equipment model.)
```

1. Leave the **ELSE / False** connector for the next step. Do not put the fallback Answer or another retrieval node on this connector; it must continue to the `Maintenance Diagnosis LLM` node in the next optional section.
2. Finish the next optional section so the ELSE / False connector leads to the `Maintenance Diagnosis LLM` and a final answer node. Then test the decision:
   - Ask `今天天气怎么样` with no equipment model. It should use the fallback Answer.
   - Ask `JX-2000A液压压力不足` with equipment model `JX-2000A`. It should use the ELSE / False connector and produce the technical answer from the LLM.

## Optional advanced route: replace the simple LLM path

This adds a second `Maintenance Diagnosis LLM` on the enhanced branch — it supersedes the simple LLM node from 2.3, which you remove from the main path once this branch works.

1. From the **ELSE / false / has data** output, add an **LLM** node named `Maintenance Diagnosis LLM`.
2. Settings:
   - Model: select your configured **DeepSeek text model**. This Chatflow uses text only; do not select an image model.
   - Temperature: `0.2`
   - Max tokens: `2000`
   - Memory: **Off** for now
3. Find the **context** section → click **+** → choose **Combined Retrieval Context / output**.
4. In the **SYSTEM** prompt box paste exactly:

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

1. In the **USER** box, use the `{x}` variable picker (do not type the braces by hand):
   - First line text: `装备型号：` then insert variable **Start → equipment_model**
   - Second line text: `故障描述：` then insert **sys.query**
2. After this LLM add an **Answer** node named `Final Maintenance Answer`, and in its message box insert the variable **Maintenance Diagnosis LLM → body/text**.

## Optional advanced route: test the enhanced Chatflow

1. Top-right of the canvas click **Debug & Preview** (a chat panel opens).
2. In the optional `equipment_model` field type `JX-2000A`, then ask: `液压压力不足`.
3. You should get the five-section Chinese answer.
4. Ask these and check behavior (note pass/fail in a Notepad table):
   - model `JX-3000B`: `发动机启动困难`
   - `E05报警代码`
   - `液压油多久换一次`
   - `传感器校准失败`
   - `JX-2000A-047这个零件是什么`
   - `今天天气怎么样` (must show the fallback sentence)
5. Fix only the 3 worst results, one change at a time: wrong documents → retrieval settings; right documents but bad answer → prompt.

## Optional advanced feature: conversation memory

1. Open the **Maintenance Diagnosis LLM** node.
2. Find **Memory** → switch **On** → **Window Size**: `3`.
3. In the debug panel test two turns:
   - Turn 1: `JX-2000A液压压力不足`
   - Turn 2: `那需要什么备件？`  
     The second answer must still be about JX-2000A hydraulics.

## Optional advanced feature: structured output and validation

1. Open the **Maintenance Diagnosis LLM** node → find **Structured Output** → switch **On**.
2. Name the validator node `Structured Output Validator` and paste this JSON schema into the schema box:

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

1. Between the LLM node and its Answer node insert a **Code** node (language **Python3**), paste:

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

1. In the Code node's **Input Variables**, add `llm_output` = the LLM node's structured output.
2. Add an **IF/ELSE** after the Code node on condition `Code / valid` **equals** `True`.
3. TRUE branch → an Answer node with this text. At each `{{...}}` position, delete the placeholder text and insert the matching variable with the `{x}` picker under **Code → data**. The placeholders below show only which variable goes where — leaving them as literal text would print the braces in the answer:

```
## 可能原因
{{possible_causes}}

## 诊断步骤
{{diagnostic_steps}}

## 维修流程
{{repair_procedure}}

## 安全警告
{{safety_warnings}}

## 参考文档
{{source_documents}}
```

1. FALSE branch → an Answer node with:

```
回答生成失败。请重试，或提供更详细的故障描述。
(Answer generation failed. Please retry with a more detailed fault description.)
```

## 2.5 Publish the minimum Chatflow

1. Top-right click **Publish**.
2. Re-run the test questions once more.
3. Get the API key (needed on Day 3): in the app's left sidebar click **API Access** → **API Key** → **Create new Secret key** → copy the `app-...` string into Notepad, label it "Chatflow key".

**Day 2 checkpoint:** at least 12 of 15 test questions answered correctly.

---

# PART 3 — Optional: workflows and automatic test

## 3.1 Workflow A — Weekly Report Generator

1. **Studio → Create from Blank → Workflow**. Name: `周报生成器 (Weekly Report)`.
2. **Start node** → under **Input Field**, click **+** and add: `week_number`, type **Short Text**, not required.
3. Add an **HTTP Request** node:
   - Method: **GET**
   - URL: `https://httpbin.org/json`
   - Timeout: `30`
4. Add a **Code** node (Python3), input variable `http_response` = HTTP body, paste:

```python
def main(http_response):
    import json

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


1. Add a **Knowledge Retrieval** node: query text `常见故障 预防性维护 高故障装备`, select Manuals + Fault Cases KBs, Top K `8`.
2. Add an **LLM** node: select your configured **DeepSeek text model**, temperature `0.3`, max tokens `2500`, context = the retrieval result, paste:

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

USER box: text `数据：` + variable **Code → summary_json**, new line `技术参考：` + the retrieval result.  
7\. Open the **Output** node (in this Dify version the end node is labelled **Output**) → output variable `report` = **LLM → text**.  
8\. Top-right click **Run**, set `week_number` to `2026-W41`, confirm a Chinese report appears → **Publish**.

## 3.2 Configure the mock HTTP tool for the Agent

The Agent needs an "equipment database" tool. We use a free echo URL as a mock.

1. Top menu click **Tools** → **Custom** → **Create Custom Tool**. This is a new Dify tool configuration; it does not create any project documents.
2. Name: `equipment_lookup`.
3. In the schema box paste:

```json
{
  "openapi": "1.0.0",
  "info": {
    "title": "Equipment Lookup",
    "version": "1.0.0"
  },
  "servers": [
    { "url": "https://httpbin.org" }
  ],
  "paths": {
    "/anything": {
      "get": {
        "operationId": "equipment_lookup",
        "summary": "look up the current status of one equipment unit",
        "parameters": [
          {
            "name": "equipment_model",
            "in": "query",
            "required": true,
            "schema": { "type": "string" },
            "description": "equipment model, e.g. JX-2000A"
          }
        ],
        "responses": { "200": { "description": "OK" } }
      }
    }
  }
}
```

1. Leave **Authorization method** as **None** (no key needed), click **Save** and confirm in the **Confirm to save ?** dialog. Optionally click **Test** next to the tool to try it.

## 3.3 Workflow B — Autonomous Diagnosis Agent

1. **Studio → Create from Blank → Workflow**. Name: `自主诊断助手 (Autonomous Diagnosis)`.
2. **Start** variables:
   - `symptom` — **Short Text**, **required**
   - `equipment_model` — **Short Text**, optional
3. Add a **Code** node (Python3), inputs `symptom` and `equipment_model` from Start:

```python
def main(symptom, equipment_model):
    if not symptom or len(symptom.strip()) < 8:
        return {"valid": False, "reason": "症状描述过短"}

    keywords = ["故障", "报警", "异常", "不足", "无法", "停机", "噪音", "压力", "温度",
                "校准", "错误", "代码", "液压", "电气", "传感器"]
    if not any(k in symptom for k in keywords):
        return {"valid": False, "reason": "描述与装备故障无关"}

    return {"valid": True, "clean_symptom": symptom.strip(),
            "model": equipment_model or "unknown"}
```

1. Add **IF/ELSE** on `Code / valid` equals `True`. FALSE → an Answer/Output node that outputs `Code / reason`.
2. TRUE → add an **Agent** node:
   - Model: select your configured **DeepSeek text model**
   - Agent strategy: **Function Calling** (if the strategy list is empty, install an agent-strategy plugin from the **Marketplace** first)
   - Max iterations: `5` (this field is provided by the strategy plugin — its label can differ)
   - Temperature: `0.2`
   - **Tools → Add Tool** → tick `equipment_lookup`
   - **Knowledge / Associated Knowledge** (if your version shows this section): add all 4 KBs. If only tools are shown, skip it — the Agent still works with the HTTP tool.
   - In the Agent's instruction box paste:

```
你是自主诊断助手。根据用户提供的故障描述，自主决定调用哪些工具来诊断。

可用工具：
- 知识库检索：查询维修技术手册、故障案例和备件目录
- equipment_lookup：查询装备状态数据库，参数为装备型号

诊断流程：
1. 先检索知识库查找相似故障
2. 如果知道装备型号，用 equipment_lookup 查询其当前状态
3. 需要更换部件时，在备件目录中查询备件编号
4. 综合所有工具结果给出诊断

规则：
- 最多调用5次工具
- 5次后仍无法确定，输出"信息不足"并列出还需要什么数据
- 每个结论都引用工具返回的证据
- 使用中文回答
```

1. Add a **Code** node after the Agent:

```python
def main(agent_output):
    output = str(agent_output)
    if "信息不足" in output or len(output) < 50:
        return {"complete": False, "output": output}
    return {"complete": True, "output": output}
```

Input: `agent_output` = Agent output.  
7\. **IF/ELSE** on `complete` → TRUE: Output/Answer with `Code / output`; FALSE: Answer asking the user for the equipment model and a more detailed symptom.  
8\. Click **Run** five times with these inputs and watch the tool-call trace:

| symptom                  | equipment_model | Expected                     |
| ------------------------ | --------------- | ---------------------------- |
| `JX-2000A液压压力不足，需要什么备件？` | JX-2000A        | knowledge + equipment_lookup |
| `E05报警代码是什么意思？`          | (empty)         | knowledge only               |
| `设备坏了`                   | (empty)         | rejected as too vague        |
| `JX-3000B频繁停机`           | JX-3000B        | knowledge + lookup           |
| `今天几号？`                  | (empty)         | rejected as out of scope     |

1. **Publish**.

## 3.4 Run the 40-question automatic evaluation

1. The evaluation script and 40 test cases are already prepared. Add your Chatflow API key to the project's `.env` file, replacing `app-PASTE_CHATFLOW_KEY_HERE`.
2. Install the test libraries once if they are not already available:

```bash
python -m pip install requests python-dotenv
```

1. Run the evaluation script:

```bash
cd /c/Users/Healer/Documents/trae_projects/dify-equipment-maintenance
python scripts/run_evaluation.py
```

1. When it finishes, open `docs\test-results.csv`.
   - Target: **30 or more of the 40 cases pass (about 75%+)**. The script auto-judges 38 of the 40.
   - Cases 13 and 14 are the remaining two: they are negative tests. Open them in Excel and mark pass manually if the answer is the fallback sentence.
2. If below target: sort the CSV by `passed=False`, group failures into "wrong retrieval" vs "bad answer" vs "validation error", fix the biggest group, then run again. Save a final copy as `docs/test-results-final.csv`.

**Day 3 checkpoint:** report workflow and agent both run; chatflow 30+/40; agent behaves on 4/5 scenarios.

---

# PART 4 — Optional: documentation

## 4.1 Write the README

1. Open `README.md` and write these headings (fill XX with your real numbers from the final CSV):
   - Title and one-line description: "Privately deployed equipment-maintenance assistant on Dify."
   - **Overview** — the three apps (Chatflow, Workflow, Agent)
   - **Knowledge Base Design** — table: Manuals 20 / Parent-child / High Quality; SOPs 10 / General / High Quality; Fault cases 10 / General / High Quality; Parts 10 / General / Economical; plus metadata fields `equipment_model, doc_type, version`
   - **Key Design Decisions** — 5 bullets: parent-child for manuals, metadata filtering, economical index for part numbers, structured output with validator, temperature 0.2
   - **Test Results** — 40 cases, pass rate XX/40, average latency, tokens per call
   - **What I Would Improve** — add a rerank model, 200+ test cases, structured database for parts, human-approval node before ERP changes

## 4.2 Complete the decision log

Open `docs/decision-log.md` and write at least 10 entries. Each entry follows this template:

```markdown
## YYYY-MM-DD — Short title of the decision

**Decision:** what you chose.
**Alternative rejected:** what else you could have done.
**Reason:** why the choice is better.
**Evidence:** numbers from a before/after test.
**Trade-off:** what it costs (tokens, speed, rebuild effort).
```

Topics to write about: chunk mode for manuals, chunk sizes per KB, hybrid retrieval, Top K = 10 and threshold 0.35, metadata filtering, Economical vs High Quality for parts, temperature values, memory window 3, structured output schema, agent max 5 iterations.

## 4.3 Take screenshots

Press **Windows + Shift + S** for each, then paste into Paint and save PNG files into `docs\screenshots\`:

- All three app canvases
- Agent run trace showing tool calls
- Retrieval Testing panel
- Knowledge base settings for all 4 KBs
- `test-results-final.csv` open in Excel

## 4.4 Export each app's DSL (optional but recommended)

In each app click the **menu (⋯ top-left or top-right)** → **Export DSL** → save the `.yml` into the project's `dsl\` folder. This lets someone re-import your apps.

---

# Minimum Completion Checklist

- [ ] Four knowledge bases show all documents **completed**
- [ ] The simple Chatflow is published
- [ ] The five basic Chatflow test questions return answers

# Optional Completion Checklist

- [ ] `equipment_model`, `doc_type`, `version` metadata set on all documents
- [ ] Advanced routing, memory, structured output, and validation are working
- [ ] Weekly report workflow runs with `2026-W41`
- [ ] Agent workflow behaves correctly on 4/5 scenarios
- [ ] `docs/test-results-final.csv` saved, 30+/40 pass
- [ ] `README.md` and `docs/decision-log.md` (10+ entries) finished
- [ ] Screenshots in `docs/screenshots/`

# Troubleshooting Quick Reference

| Problem                              | Fix                                                                      |
| ------------------------------------ | ------------------------------------------------------------------------ |
| Documents stay at "waiting"          | Wait for indexing to finish, then refresh the knowledge base             |
| Retrieval returns wrong model's docs | Check the metadata filter node and per-document metadata values          |
| Chatflow answer ignores structure    | Confirm Context points to the Aggregator output and Memory is On         |
| Agent never calls the tool           | Check the tool is ticked in the Agent node and "先检索知识库" is in its prompt |
| API returns HTTP 401                 | The key in `.env` is wrong or missing `app-` prefix                      |

