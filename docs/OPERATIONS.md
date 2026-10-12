# Operations and Production Readiness

## Deployment checklist

- Import the DSL into the target Dify workspace.
- Verify all dataset IDs, metadata fields, model providers, embedding model, and model versions.
- Configure the Chat API key and base URL through a secret store or local `.env`; never put them in Git.
- Configure HTTPS, endpoint authentication, workspace roles, rate limits, conversation retention, and log access.
- Run the full evaluation and archive the sanitized CSV and JSON summary with the deployed DSL version.
- Obtain owner approval for the acceptance result and known limitations before release.

## Acceptance criteria

The default evaluator acceptance gate is:

- At least 80% of positive cases pass the keyword relevance check.
- 100% of negative cases return a recognized no-results or generation-failure fallback.
- No evaluation case exposes a credential or claims that a physical action was completed.
- Average latency and token usage are recorded for comparison; establish a service-specific p95 target before production rollout.

These are prototype gates, not a substitute for human safety review or domain expert evaluation.

## Monitoring

Track, at minimum, workflow success/failure counts, fallback counts, validation failures, API error categories, latency p50/p95, token usage, retrieval score distribution, model and prompt versions, and evaluation pass rate. Alert on repeated API failures, a sudden increase in fallback or validation failures, acceptance-rate regression, or abnormal token/cost growth.

Logs must avoid raw credentials and unnecessary sensitive user content. Use a correlation ID and retain only the minimum data needed for diagnosis.

## Incident procedures

1. Classify the incident as availability, quality, security/privacy, or safety.
2. For unsafe advice, disable the chatflow or route all requests to human review.
3. For availability issues, verify Dify, model, embedding, and dataset health; retry only idempotent reads.
4. For quality regressions, compare the current DSL, prompt, dataset, and model versions against the last accepted evaluation.
5. Record the cause, affected versions, mitigation, owner, and follow-up regression test.

## Backup and rollback

Store versioned copies of the DSL, prompt files, dataset manifests, evaluation cases, and sanitized evaluation results. Roll back by importing the last accepted DSL and restoring the matching prompt and knowledge-base version. Do not restore secrets from Git or evaluation artifacts.

## Change management

Every change to prompts, retrieval settings, datasets, models, or evaluator logic must have a review, a targeted test, and a full evaluation before publishing. Keep the deployed DSL version and evaluation summary together.
