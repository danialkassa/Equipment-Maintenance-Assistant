# Architecture

## Purpose and scope

The Equipment Maintenance Assistant answers Chinese-language maintenance questions using the Dify knowledge base. It is an advisory system for diagnosis and maintenance guidance. It does not control equipment, execute repairs, change settings, order parts, or replace an authorized technician.

## Data flow

1. The user submits a question and may provide an equipment model.
2. The workflow selects either model-filtered retrieval or all-model retrieval.
3. Retrieved manuals, parts information, SOPs, and fault cases are combined as context.
4. If no relevant context is found, the workflow returns a bilingual no-results response.
5. The LLM produces structured causes, diagnostic steps, repair procedure, safety warnings, and source documents.
6. A code node validates required fields and formats the final Markdown response.
7. Invalid model output reaches a safe retry/incomplete-answer response instead of being rendered.

The workflow definition is exported in `dsl/Equipment Maintenance Assistant.yml`.

## Component responsibilities

- Dify: workflow orchestration, retrieval, model invocation, conversation handling, and execution logs.
- Knowledge base: authoritative maintenance manuals, parts data, SOPs, and fault cases under `data/dify-docs/`.
- LLM: language interpretation and answer drafting only; it must not invent procedures or claim physical actions.
- Structured-output validator: checks required fields and prevents malformed answers from reaching the user.
- Evaluation client: `scripts/run_evaluation.py` calls the Dify Chat API and records quality, latency, token, and failure results.

## Boundaries and failure behavior

- Empty retrieval returns the no-results fallback.
- Empty, malformed, or incomplete structured output returns the validation-failure fallback.
- API timeout, connection failure, and transient HTTP failures are retried by the evaluation client; the Dify workflow itself has no autonomous external action to retry.
- Conflicting or missing source information must be disclosed rather than resolved by unsupported assumptions.
- High-risk work requires equipment isolation and an authorized technician.

## Dependencies

- Dify Chat API and a deployed chatflow.
- DeepSeek chat model configured in Dify.
- Ollama embedding model `nomic-embed-text` configured in Dify.
- Python 3.9+ with `requests` and `python-dotenv` for evaluation.

## Known limitations

The current export contains provider and dataset identifiers but not a deployable Dify server configuration. Dataset IDs must be replaced or verified in the target Dify workspace. No external repair, inventory, CMMS, or approval integration is present.
