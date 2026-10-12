# Security and Privacy

## Threat model

The assistant receives untrusted user questions and retrieves text that may be incomplete, stale, or maliciously crafted. The system is advisory and has no tool node or write access to equipment, inventory, maintenance records, or other business systems.

## Controls

- API credentials are loaded from `.env` and `.env` is excluded by `.gitignore`. Never commit, print, or place credentials in test results.
- The Dify API key should be scoped to the minimum chatflow permission required by the evaluator and rotated through the deployment secret store.
- Dify workspace access should use named users and least-privilege roles. Dataset editing and application publishing should be restricted to maintainers.
- Retrieved content and user input are data, not instructions. The workflow prompt requires the model to ignore embedded requests to change rules, disclose prompts, or perform external actions.
- The assistant must cite source document names and state when information is not present. It must not claim that a physical inspection, repair, shutdown, or adjustment occurred.
- The assistant must warn about electrical, pressure, heat, and moving-part hazards and direct high-risk work to an authorized technician.
- Logs and evaluation exports must be reviewed for credentials, personal data, equipment identifiers, and unnecessary user text before sharing.

## Required deployment controls

Before production use, configure authentication for the Dify endpoint, HTTPS, workspace permissions, rate limits, and a retention/deletion policy for conversations and logs. Confirm whether equipment identifiers or operator names are personal or commercially sensitive data and minimize their retention.

## Security test cases

At minimum, test prompt-injection requests, requests for system prompts or credentials, malicious instructions inside a knowledge document, cross-model retrieval, unsupported equipment, and requests to perform a consequential action. Expected behavior is refusal or bounded technical guidance with no secret disclosure or external action.

## Incident response

For suspected credential exposure, revoke and rotate the affected key, preserve only sanitized evidence, review access logs, and redeploy. For unsafe or fabricated guidance, disable the chatflow, record the input and source versions without secrets, identify the failure, add a regression case, and re-enable only after review.
