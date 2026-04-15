#!/usr/bin/env bash
# Windows Python Environment Minification Script

set -e

echo "========================================================"
echo "     Python Environment Minification Script (Windows)"
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
LIB_DIR="$TARGET_DIR/Lib"
DLLS_DIR="$TARGET_DIR/DLLs"
SITE_PACKAGES="$LIB_DIR/site-packages"

echo "PWD.. $PWD"
echo "TARGET_DIR.. $TARGET_DIR"

echo "[1/9] Removing Debugging Symbols (*.pdb)..."
find "$TARGET_DIR" -type f -name "*.pdb" -delete

echo "[2/9] Removing C-Headers and Static Libraries..."
rm -rf "$TARGET_DIR/include" "$TARGET_DIR/libs"
if [ -d "$DLLS_DIR" ]; then find "$DLLS_DIR" -type f -name "*.lib" -delete; fi

echo "[3/9] Removing Python Standard Library Tests..."
rm -rf "$LIB_DIR/test" "$LIB_DIR/idle_test"

echo "[4/9] Removing Tkinter and Tcl (GUI Framework)..."
rm -rf "$TARGET_DIR/tcl"
rm -rf "$LIB_DIR/tkinter" "$LIB_DIR/idlelib" "$LIB_DIR/turtledemo"
rm -f "$DLLS_DIR/_tkinter.pyd"
rm -f "$DLLS_DIR"/tcl8*.dll "$DLLS_DIR"/tk8*.dll

echo "[5/9] Removing Package Managers (pip, setuptools, venv)..."
rm -rf "$LIB_DIR/ensurepip" "$LIB_DIR/venv"
rm -rf "$SITE_PACKAGES/pip"* "$SITE_PACKAGES/setuptools"*

echo "[6/9] Removing Third-Party Package Tests..."
rm -rf "$SITE_PACKAGES/pandas/tests"
find "$SITE_PACKAGES/numpy" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
rm -rf "$SITE_PACKAGES/polars/testing" "$SITE_PACKAGES/sqlalchemy/testing"
rm -rf "$SITE_PACKAGES/colorama/tests" "$SITE_PACKAGES/greenlet/tests"

echo "[7/9] Removing CPython Internal C-Extension Tests..."
for ext in _ctypes_test.pyd _testbuffer.pyd _testcapi.pyd _testclinic.pyd \
           _testconsole.pyd _testimportmultiple.pyd _testinternalcapi.pyd \
           _testmultiphase.pyd _testsinglephase.pyd; do
    rm -f "$DLLS_DIR/$ext"
done

echo "[8/9] Removing Uncompiled Source Files..."
if [ -d "$SITE_PACKAGES" ]; then
    find "$SITE_PACKAGES" -type f \( -name "*.c" -o -name "*.cpp" -o -name "*.pyx" -o -name "*.lib" \) -delete
fi

echo "[9/9] Removing Intermediate PyCache Directories..."
find "$TARGET_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +

echo ""
echo "Cleanup complete! Your Windows distribution is now optimized."