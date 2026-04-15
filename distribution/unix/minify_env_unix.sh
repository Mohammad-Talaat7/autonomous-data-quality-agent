#!/usr/bin/env bash
# Linux / macOS Python Environment Minification Script

set -e

echo "========================================================"
echo "   Python Environment Minification Script (Linux/macOS)"
echo "========================================================"
echo "WARNING: This permanently deletes debugging symbols, tests,"
echo "static libraries, unused GUI libraries, and build files."
echo ""

if [ "$1" != "-y" ]; then
    read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then echo "Cleanup aborted."; exit 1; fi
fi

TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
STRIP_CMD="${STRIP:-strip}"

echo "PWD.. $PWD"
echo "TARGET_DIR.. $TARGET_DIR"

# Auto-detect Python lib directory (e.g., lib/python3.11)
LIB_DIR=$(find "$TARGET_DIR/lib" -maxdepth 1 -type d -name "python3.*" | head -n 1)
if [ -z "$LIB_DIR" ]; then echo "Error: Could not find lib/python3.* directory."; exit 1; fi
DYNLOAD_DIR="$LIB_DIR/lib-dynload"
SITE_PACKAGES="$LIB_DIR/site-packages"

echo "[1/9] Stripping Debugging Symbols from Binaries..."
# Strip shared libraries and C-extensions
find "$TARGET_DIR" \( -name '*.so' -o -name '*.dylib' \) -type f -print0 | xargs -0 -I {} "$STRIP_CMD" --strip-unneeded "{}" 2>/dev/null || true
# Strip executables in bin/
if [ -d "$TARGET_DIR/bin" ]; then
    find "$TARGET_DIR/bin" -type f -executable -print0 | while IFS= read -r -d '' file; do
        if file "$file" | grep -Eq 'ELF|Mach-O'; then "$STRIP_CMD" --strip-all "$file" 2>/dev/null || true; fi
    done
fi

echo "[2/9] Removing C-Headers and Static Libraries..."
rm -rf "$TARGET_DIR/include"
find "$TARGET_DIR" -type f -name "*.a" -delete

echo "[3/9] Removing Python Standard Library Tests..."
rm -rf "$LIB_DIR/test" "$LIB_DIR/idle_test"

echo "[4/9] Removing Tkinter and Tcl (GUI Framework)..."
rm -rf "$LIB_DIR/tkinter" "$LIB_DIR/idlelib" "$LIB_DIR/turtledemo"
rm -f "$DYNLOAD_DIR/_tkinter"*.so

echo "[5/9] Removing Package Managers (pip, setuptools, venv)..."
rm -rf "$LIB_DIR/ensurepip" "$LIB_DIR/venv"
rm -rf "$SITE_PACKAGES/pip"* "$SITE_PACKAGES/setuptools"*

echo "[6/9] Removing Third-Party Package Tests..."
rm -rf "$SITE_PACKAGES/pandas/tests"
find "$SITE_PACKAGES/numpy" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
rm -rf "$SITE_PACKAGES/polars/testing" "$SITE_PACKAGES/sqlalchemy/testing"
rm -rf "$SITE_PACKAGES/colorama/tests" "$SITE_PACKAGES/greenlet/tests"

echo "[7/9] Removing CPython Internal C-Extension Tests..."
for ext in _ctypes_test _testbuffer _testcapi _testclinic \
           _testconsole _testimportmultiple _testinternalcapi \
           _testmultiphase _testsinglephase; do
    rm -f "$DYNLOAD_DIR/$ext"*.so
done

echo "[8/9] Removing Uncompiled Source Files..."
if [ -d "$SITE_PACKAGES" ]; then
    find "$SITE_PACKAGES" -type f \( -name "*.c" -o -name "*.cpp" -o -name "*.pyx" \) -delete
fi

echo "[9/9] Removing Intermediate PyCache Directories..."
find "$TARGET_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +

echo ""
echo "Cleanup complete! Your Unix distribution is now optimized."