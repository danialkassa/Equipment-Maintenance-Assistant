# Business Value and Measurement

## Problem

Maintenance personnel need faster access to scattered manuals, parts information, SOPs, and historical fault cases. The assistant is intended to reduce search time and improve consistency of first-line technical guidance while keeping consequential work with authorized personnel.

## Measures to establish before production

Capture a baseline over representative maintenance requests:

- Median time to locate relevant technical information.
- Time from question to a usable, source-backed answer.
- First-line resolution or correct-escalation rate.
- Rework caused by missing or incorrect information.
- Human review time per answer.
- Model, infrastructure, and maintenance cost per request.
- User-rated usefulness and trust in source citations.

Compare these measures with the assistant enabled and with the current manual process. Report confidence intervals or sample sizes for material decisions.

## Suitability and boundaries

AI is appropriate for retrieving and organizing language-heavy documentation. Deterministic controls remain preferable for inventory transactions, equipment control, safety interlocks, approvals, and any operation that changes real-world state. The current project intentionally performs no such actions.

## Value decision

Proceed beyond prototype only if source-backed answer quality, response time, adoption, human-review effort, and operating cost meet stakeholder-approved targets without increasing safety or privacy risk. Reassess these measures after significant model, prompt, data, or workflow changes.
