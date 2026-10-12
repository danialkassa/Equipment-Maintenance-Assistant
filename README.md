# Equipment Maintenance Assistant

A Dify knowledge-base and evaluation project for answering equipment maintenance questions from manuals, parts catalogs, standard operating procedures, and fault cases.

## Project contents

- `data/dify-docs/`: source documents organized by manuals, parts, SOPs, and fault cases
- `dsl/`: Dify application DSL export
- `tests/test_cases.csv`: evaluation cases
- `scripts/`: evaluation utilities
- `setup/`: setup scripts for preparing the project
- `docs/`: project documentation and screenshots
- `instructionsDify*.md`: prompts and implementation notes

## Requirements

Python 3.9+ and the packages listed in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
```

Keep local credentials and environment configuration in `.env`; it is intentionally excluded from version control.
