# Contributing to ADQA

Thank you for your interest in contributing to ADQA! We welcome contributions from the community to make data quality analysis more autonomous and robust.

## How to Contribute

### 1. Reporting Bugs
- Use the [Bug Report Template](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/issues/new?template=bug_report.md).
- Provide a clear description of the issue and steps to reproduce.
- Include environment details (OS, Python version, ADQA version).

### 2. Suggesting Enhancements
- Use the [Feature Request Template](https://github.com/Mohammad-Talaat7/autonomous-data-quality-agent/issues/new?template=feature_request.md).
- Explain the use case and why this feature would be valuable.

### 3. Code Contributions
- Fork the repository.
- Create a new branch (`feature/my-feature` or `fix/my-bug`).
- **Development Setup**:
  ```bash
  pip install poetry
  poetry install --with dev
  ```
- **Run Tests**:
  ```bash
  poetry run pytest
  ```
- **Linting**:
  We use `ruff` and `mypy`. Ensure they pass before submitting:
  ```bash
  poetry run ruff check .
  poetry run mypy src/adqa
  ```
- Submit a Pull Request.

## Architecture Overview

ADQA is modular. If you want to add a new detector:
1. Create a new class inheriting from `BaseDetector` or `ColumnDetector` in `src/adqa/detection/rule_detectors/`.
2. Register it in `src/adqa/detection/registry_setup.py`.
3. Add a test case in `tests/detection/`.

## Style Guide
- Follow PEP 8.
- Use type hints for all new functions.
- Add docstrings (Google style) to all public classes and methods.

## Code of Conduct
Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).
