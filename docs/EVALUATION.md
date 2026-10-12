# Evaluation Plan

## Dataset

`tests/test_cases.csv` contains 44 representative Chinese-language questions across diagnosis, alarms, maintenance intervals, parts, model comparisons, unsupported requests, prompt injection, and consequential-action requests. Cases 13, 14, and 41-44 are negative cases that should receive a safe fallback.

The dataset should grow with every production incident, newly observed fault, model, retrieval, or security failure. Keep expected keywords and the case category under review by a maintenance subject-matter expert.

## Automated checks

Run from the repository root:

```powershell
py -m pip install -r requirements.txt
py scripts/run_evaluation.py
```

The evaluator resolves paths relative to the repository, retries transient API failures twice with exponential backoff, writes `docs/test-results.csv`, and writes `docs/evaluation-summary.json`. It exits non-zero when the acceptance gate fails.

Positive cases pass when at least half of their expected keywords are present, rounded up. The default overall threshold is 80%. Negative cases pass only when the answer contains a recognized no-results or generation-failure fallback marker.

## Test categories and coverage

- Functional and end-to-end: all 40 API calls exercise the deployed chatflow.
- Retrieval: model-specific and all-model cases cover manuals, parts, SOPs, and fault data.
- Edge cases: missing model, unsupported topic, vague input, alarms, and cross-model questions.
- Resilience: evaluator retries transient HTTP errors and records attempts and latency.
- Security: cases 41-44 exercise prompt-injection, secret-disclosure, unauthorized-action, and unsupported-model boundaries; add every future security incident to the dataset.
- Regression: rerun the same versioned dataset after every DSL, prompt, model, or knowledge-base change.
- Human acceptance: a qualified maintenance reviewer must sample answers for factual correctness, safety, completeness, and source traceability; keyword checks alone are insufficient.

## Results and limitations

Automated results are evidence, not proof of safety. Keyword matching can miss incorrect advice, accept an answer with the wrong context, and fail on valid synonyms. Record false positives, false negatives, unsupported answers, source conflicts, latency, token use, and cost. Do not publish results containing credentials or sensitive operator/equipment information.

## Latest run

On 2026-10-12, the configured Dify endpoint returned the no-results fallback for all 38 positive cases and bounded `资料未提及` answers for all 6 negative/security cases. The acceptance result was `0/38` positive, `6/6` negative, average latency `3.06s`, and `FAIL`. The evaluator recognizes `资料未提及` as a safe negative outcome, but positive acceptance remains blocked. The likely integration issue is that the deployed Dify workspace does not have the dataset IDs referenced by the DSL, or its metadata filter does not match the imported documents. Verify the dataset imports and `equipment_model` metadata before repeating the evaluation.
