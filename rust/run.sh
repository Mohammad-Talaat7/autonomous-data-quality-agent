#!/usr/bin/env bash
set -e

# Move to the project root (parent of this script's directory).
cd "$(dirname "$0")/.."

# Pre-flight: make sure the poetry venv is set up before doing anything else.
# These checks fail fast with a clear, actionable message instead of letting
# the failure surface as a cryptic ModuleNotFoundError 30 seconds in.
if ! command -v poetry >/dev/null 2>&1; then
    echo "poetry is not installed or not on PATH." >&2
    echo "Install it: https://python-poetry.org/docs/#installation" >&2
    exit 1
fi
if ! poetry env info -p >/dev/null 2>&1; then
    echo "No poetry virtualenv exists for this project." >&2
    echo "Run: poetry install" >&2
    exit 1
fi
if ! poetry run python -c "import adqa; assert adqa.__file__" >/dev/null 2>&1; then
    echo "adqa is not properly installed in the poetry venv." >&2
    echo "Run: poetry install" >&2
    exit 1
fi

# Ask the user which UI to run.
echo "Which UI would you like to run?"
echo "  1) cli   (adqa-cli)"
echo "  2) tui   (adqa-tui)"
echo "  3) slint (adqa-slint)"
read -r -p "Enter choice [1-3 or name]: " choice

case "$choice" in
    1|cli)    BIN="adqa-cli"   ;;
    2|tui)    BIN="adqa-tui"   ;;
    3|slint)  BIN="adqa-slint" ;;
    *) echo "Invalid choice: $choice" >&2; exit 1 ;;
esac

# Tell pyo3 which Python to build against (the venv's interpreter).
export PYO3_PYTHON="$(poetry env info -p)/bin/python"

echo "==> Building $BIN"
cargo build --manifest-path rust/Cargo.toml --bin "$BIN"

# libpython3.12.so.1.0 lives in the *base* Python's lib (the relocatable
# venv doesn't copy it). sys.base_prefix points at the pyenv/system install.
export LD_LIBRARY_PATH="$(poetry run python -c 'import sys; print(sys.base_prefix)')/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

echo "==> Running $BIN"
exec poetry run bash -c "./rust/target/debug/$BIN $*"
