# Equipment Maintenance Assistant

A Dify knowledge-base and evaluation project for answering equipment maintenance questions from manuals, parts catalogs, standard operating procedures, and fault cases.

## Project contents

- `data/dify-docs/`: source documents organized by manuals, parts, SOPs, and fault cases
- `dsl/`: Dify application DSL export
- `tests/test_cases.csv`: evaluation cases
- `tests/standard.md`: engineering and production-readiness standard used for review
- `scripts/`: evaluation utilities
- `setup/`: setup scripts for preparing the project
- `docs/`: project documentation and screenshots
- `instructionsDify*.md`: prompts and implementation notes

Engineering documentation is available in `docs/ARCHITECTURE.md`, `docs/SECURITY.md`,
`docs/OPERATIONS.md`, `docs/EVALUATION.md`, and `docs/BUSINESS-VALUE.md`.

## Requirements

Python 3.9+ and the packages listed in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
```

Run the evaluation from any working directory with the `py` launcher on Windows:

```powershell
py scripts/run_evaluation.py
```

The evaluator writes `docs/test-results.csv` and `docs/evaluation-summary.json`.
It exits with a non-zero status unless positive cases meet the configured 80% threshold
and all negative cases receive a documented fallback response.

Keep local credentials and environment configuration in `.env`; it is intentionally excluded from version control.
