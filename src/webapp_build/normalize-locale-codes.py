#!/usr/bin/env python3
"""
Normalize i18n locale codes to lowercase.

This script fixes case sensitivity issues in language detection by converting
all language code keys to lowercase while preserving translation content.

The detectLanguage() function converts navigator.language to lowercase, so
all language codes in TRANSLATIONS and LOCALE_FALLBACK must also be lowercase.
"""

import re
import sys

def normalize_i18n_file(filepath):
    """Normalize language codes in i18n JavaScript file."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = 0

    # Pattern 1: Language object keys in TRANSLATIONS/ADDITIONAL_TRANSLATIONS
    # Matches:  en: {  or  "en": {  or  'en': {
    # Also:     en-US: {  or  "zh-Hans": {
    def replace_lang_key(match):
        nonlocal changes_made
        quote = match.group(1) or ''  # Optional quote
        lang_code = match.group(2)    # Language code
        rest = match.group(3)          # : {

        lower_code = lang_code.lower()
        if lang_code != lower_code:
            changes_made += 1
            print(f"  {lang_code} → {lower_code}")

        return f"{quote}{lower_code}{quote}{rest}"

    # Pattern: optional quote, language code (2-3 letters with optional -Script-Region), optional quote, colon, optional space, opening brace
    # Examples: en: {  "zh-Hans": {  'mn-Mong': {  sr-Cyrl: {
    pattern = r'''
        (?:^|\n)           # Start of line
        \s+                # Indentation
        (["'])?            # Optional opening quote (group 1)
        ([a-z]{2,3}(?:-[A-Z][a-z]+)?(?:-[A-Z]{2})?)  # Language code (group 2)
        (["'])?            # Optional closing quote (should match group 1)
        (\s*:\s*\{)        # Colon, optional space, opening brace (group 4)
    '''

    content = re.sub(
        r'''(?:^|\n)(\s+)(["'])?([a-z]{2,3}(?:-[A-Z][a-z]+)?(?:-[A-Z]{2})?)(["'])?(\s*:\s*\{)''',
        lambda m: f"\n{m.group(1)}{m.group(2) or ''}{m.group(3).lower()}{m.group(4) or ''}{m.group(5)}",
        content
    )

    # Pattern 2: Language codes in LOCALE_FALLBACK map
    # Matches: 'en-US': 'en'  or  "zh-CN": "zh-Hans"
    def replace_fallback_entry(match):
        nonlocal changes_made
        indent = match.group(1)
        from_quote = match.group(2)
        from_code = match.group(3)
        to_quote = match.group(4)
        to_code = match.group(5)
        comment = match.group(6) or ''

        from_lower = from_code.lower()
        to_lower = to_code.lower()

        if from_code != from_lower or to_code != to_lower:
            changes_made += 1
            print(f"  Fallback: {from_code} → {from_lower}, {to_code} → {to_lower}")

        return f"{indent}{from_quote}{from_lower}{from_quote}: {to_quote}{to_lower}{to_quote},{comment}"

    # Match fallback entries: 'key': 'value',
    content = re.sub(
        r'''(\s+)(['"])([a-z]{2,3}(?:-[A-Z][a-z]+)?(?:-[A-Z]{2})?)\2:\s*(['"])([a-z]{2,3}(?:-[A-Z][a-z]+)?(?:-[A-Z]{2})?)\4,(\s*//.*)?''',
        replace_fallback_entry,
        content,
        flags=re.IGNORECASE
    )

    # Pattern 3: Language names in LANGUAGE_NAMES constant
    # Matches: 'zh-Hans': '简体中文'  but only lowercase the key, not the value
    def replace_lang_name(match):
        nonlocal changes_made
        indent = match.group(1)
        key_quote = match.group(2)
        key_code = match.group(3)
        val_quote = match.group(4)
        val_name = match.group(5)
        comma = match.group(6) or ''

        key_lower = key_code.lower()

        if key_code != key_lower:
            changes_made += 1
            print(f"  Language name: {key_code} → {key_lower}")

        return f"{indent}{key_quote}{key_lower}{key_quote}: {val_quote}{val_name}{val_quote}{comma}"

    # Match in LANGUAGE_NAMES object
    content = re.sub(
        r'''(\s+)(['"])([a-z]{2,3}(?:-[A-Z][a-z]+)?(?:-[A-Z]{2})?)\2:\s*(['"])(.*?)\4(,?)''',
        replace_lang_name,
        content
    )

    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Normalized {changes_made} language codes in {filepath}")
        return True
    else:
        print(f"  No changes needed")
        return False

def normalize_build_py(filepath):
    """Normalize language codes in build.py."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changes_made = 0

    # In build.py, we need to lowercase codes in:
    # 1. LANGUAGE_NAMES dictionary
    # 2. mongolianRelevantRegions arrays
    # 3. String literals checking language codes

    # Pattern 1: LANGUAGE_NAMES entries like 'zh-Hans': '简体中文',
    def replace_lang_name_py(match):
        nonlocal changes_made
        indent = match.group(1)
        quote = match.group(2)
        code = match.group(3)
        val_quote = match.group(4)
        name = match.group(5)
        comma = match.group(6) or ''

        code_lower = code.lower()
        if code != code_lower:
            changes_made += 1
            print(f"  {code} → {code_lower}")

        return f"{indent}{quote}{code_lower}{quote}: {val_quote}{name}{val_quote}{comma}"

    content = re.sub(
        r'''(\s+)(['"])([a-z]{2,3}(?:-[a-z]+)?(?:-[a-z]{2})?)(['"]):\s*(['"])(.*?)\5(,?)''',
        replace_lang_name_py,
        content,
        flags=re.IGNORECASE
    )

    # Pattern 2: Array literals like ['mn-Mong', 'zh-Hans']
    def replace_array_code(match):
        nonlocal changes_made
        quote = match.group(1)
        code = match.group(2)

        code_lower = code.lower()
        if code != code_lower:
            changes_made += 1
            print(f"  Array element: {code} → {code_lower}")

        return f"{quote}{code_lower}{quote}"

    content = re.sub(
        r'''(['"])([a-z]{2,3}(?:-[a-z]+)?(?:-[a-z]{2})?)\1''',
        replace_array_code,
        content,
        flags=re.IGNORECASE
    )

    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Normalized {changes_made} language codes in {filepath}")
        return True
    else:
        print(f"  No changes needed")
        return False

def main():
    files = [
        'i18n.js',
        'i18n-languages.js',
        'build.py'
    ]

    any_changes = False

    for filename in files:
        if filename.endswith('.js'):
            if normalize_i18n_file(filename):
                any_changes = True
        elif filename.endswith('.py'):
            if normalize_build_py(filename):
                any_changes = True

    print()
    if any_changes:
        print("✅ Normalization complete! Language codes are now lowercase.")
        print("   Run 'python3 build.py' to rebuild with fixed language detection.")
    else:
        print("✅ All language codes are already lowercase.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
