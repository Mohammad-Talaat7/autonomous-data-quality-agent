# Project Instructions for Gemini CLI

## Project Overview
**Name**: adqa (Autonomous Data Quality Agent)
**Goal**: Build an autonomous agent for profiling, detection, explanation, and fix proposals for data quality issues.
**Python Version**: 3.12+
**Dependency Manager**: Poetry

## Core Mandates
1.  **Strict Typing**: All code must be fully typed. Use `mypy` strict mode standards.
2.  **Pydantic V2**: Use Pydantic v2 for all data models.
3.  **Path Handling**: Use `pathlib` for all file system interactions.
4.  **Logging**: Use `loguru` for logging. Do not use standard `logging`.
5.  **Dataframes**: Support both `pandas` and `polars`. When generic, prefer `polars` for performance, or abstract interactions.

## Architecture
- **`src/adqa/core`**: Core logic for agent controller, datasource management, and base models.
- **`src/adqa/llm`**: LLM interaction layer (using `litellm`).
- **`src/adqa/agents`**: Specialized sub-agents.

## Testing
- Use `pytest` with `pytest-cov`.
- All new features must have accompanying unit tests in `tests/`.
- Mock external LLM calls and Database connections.

## Git Workflow
- Commit messages should be semantic (e.g., `feat: ...`, `fix: ...`, `chore: ...`).
