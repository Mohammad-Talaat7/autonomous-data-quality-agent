# Code Style Guidelines

## Formatting
- **Formatter**: `black`
- **Line Length**: 88 characters

## Linting
- **Linter**: `ruff`
- **Rules**:
    - `E` (pycodestyle errors)
    - `F` (Pyflakes)
    - `I` (isort imports)
    - `B` (flake8-bugbear)
    - `UP` (pyupgrade)

## Type Checking
- **Tool**: `mypy`
- **Configuration**: `strict = true`
- **Requirements**:
    - explicit `Optional` handling.
    - No `Any` unless absolutely necessary (must be commented).
    - `return` types for all functions/methods.

## Docstrings
- Format: Google Style
- Required for:
    - All public modules
    - All public classes
    - All public methods/functions

## Imports
- Sorted by `ruff` (isort compatible).
- Grouping:
    1. Standard Library
    2. Third Party
    3. Local Application
