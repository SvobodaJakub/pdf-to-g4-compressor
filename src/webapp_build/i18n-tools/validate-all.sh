#!/bin/bash
#
# Comprehensive i18n Translation Validation
#
# Runs both validators for complete coverage:
# 1. JavaScript validator (authoritative, structural checks)
# 2. Python validator (semantic and linguistic checks)
#
# Usage: ./i18n-tools/validate-all.sh
#        or: cd i18n-tools && ./validate-all.sh

set -e  # Exit on first error

# Detect if we're in i18n-tools or parent directory
if [ "$(basename "$PWD")" = "i18n-tools" ]; then
    cd ..
fi

echo "======================================================================"
echo "Running Comprehensive i18n Translation Validation"
echo "======================================================================"
echo

# Run JavaScript validator (authoritative)
echo "========================================"
echo "Step 1/2: Structural Validation (JS)"
echo "========================================"
echo
node i18n-tools/i18n-validate.js
JS_EXIT=$?

echo
echo

# Run Python validator (semantic checks)
echo "========================================"
echo "Step 2/2: Semantic Validation (Python)"
echo "========================================"
echo
python3 i18n-tools/i18n-validate-legacy.py
PY_EXIT=$?

echo
echo "======================================================================"
echo "FINAL RESULT"
echo "======================================================================"

if [ $JS_EXIT -eq 0 ] && [ $PY_EXIT -eq 0 ]; then
    echo "✅ ALL VALIDATIONS PASSED"
    echo
    echo "  - Structural validation: ✅ PASS"
    echo "  - Semantic validation:   ✅ PASS"
    echo
    echo "All 83 languages are valid and complete!"
    exit 0
else
    echo "❌ VALIDATION FAILED"
    echo
    [ $JS_EXIT -ne 0 ] && echo "  - Structural validation: ❌ FAIL (fix required)"
    [ $JS_EXIT -eq 0 ] && echo "  - Structural validation: ✅ PASS"
    [ $PY_EXIT -ne 0 ] && echo "  - Semantic validation:   ⚠️  WARNINGS (review recommended)"
    [ $PY_EXIT -eq 0 ] && echo "  - Semantic validation:   ✅ PASS"
    echo
    echo "Please review and fix the issues above."
    exit 1
fi
