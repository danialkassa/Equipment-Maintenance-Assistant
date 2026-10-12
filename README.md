# Equipment Maintenance Assistant

A portfolio demonstration of an AI automation project built with Dify. It shows how to create a reusable equipment-maintenance assistant that answers questions from manuals, parts catalogs, standard operating procedures, and fault cases. It is designed to demonstrate engineering skills to potential employers and clients, not to represent one specific company's internal system.

## Project contents

- `data/dify-docs/`: source documents organized by manuals, parts, SOPs, and fault cases
- `dsl/`: Dify application DSL export
- `tests/test_cases.csv`: evaluation cases
- `tests/standard.md`: engineering and production-readiness standard used for review
- `scripts/`: evaluation utilities
- `setup/`: setup scripts for preparing the project
- `docs/`: project documentation and screenshots

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

## Portfolio purpose

This project demonstrates knowledge-base design, retrieval-augmented generation, workflow branching, structured AI output, safety boundaries, evaluation, documentation, and production-readiness thinking. The sample equipment documents provide realistic content for the demonstration and can be replaced with another organization's documents for a future implementation.
