#!/usr/bin/env python3
"""
Normalize i18n locale codes to proper BCP 47 casing.

BCP 47 convention:
  - Language subtag: lowercase (e.g., en, zh, mn)
  - Script subtag (4 letters): Title case (e.g., Hans, Mong, Cyrl, Latn)
  - Region subtag (2 letters): UPPERCASE (e.g., US, CN, MN)

The detectLanguage() function normalizes browser locale strings to BCP 47 casing
via normalizeBCP47(), so all keys in TRANSLATIONS and LOCALE_FALLBACK must also
use proper BCP 47 casing.
"""

import re
import sys


def normalize_bcp47(tag):
    """Normalize a locale tag to proper BCP 47 casing."""
    parts = tag.split('-')
    parts[0] = parts[0].lower()
    for i in range(1, len(parts)):
        if len(parts[i]) == 4:
            # Script subtag: Title case
            parts[i] = parts[i][0].upper() + parts[i][1:].lower()
        elif len(parts[i]) == 2:
            # Region subtag: UPPERCASE
            parts[i] = parts[i].upper()
        else:
            # Other (variant, extension, 3-letter language): lowercase
            parts[i] = parts[i].lower()
    return '-'.join(parts)


def normalize_i18n_file(filepath):
    """Normalize language codes in i18n JavaScript file to proper BCP 47."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changes_made = 0

    # Pattern: language code as object key — quoted or unquoted, followed by ': {'
    # Matches: en: {  "zh-hans": {  'mn-mong': {  sr-Cyrl: {
    def replace_key(match):
        nonlocal changes_made
        indent = match.group(1)
        q1 = match.group(2) or ''
        code = match.group(3)
        q2 = match.group(4) or ''
        rest = match.group(5)

        normalized = normalize_bcp47(code)
        if code != normalized:
            changes_made += 1
            print(f"  Key: {code} → {normalized}")

        return f"\n{indent}{q1}{normalized}{q2}{rest}"

    content = re.sub(
        r'\n(\s+)(["']?)([a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?(?:-[a-zA-Z]{2})?)\2(\s*:\s*\{)',
        lambda m: replace_key(type('', (), {'group': m.group})()),
        content
    )
    # Simpler approach: just use sub with the match object directly
    content_orig = content

    # Pattern for fallback entries: 'key': 'value',
    def replace_fallback(m):
        nonlocal changes_made
        indent = m.group(1)
        q = m.group(2)
        from_code = m.group(3)
        vq = m.group(4)
        to_code = m.group(5)
        comment = m.group(6) or ''

        from_norm = normalize_bcp47(from_code)
        to_norm = normalize_bcp47(to_code)

        if from_code != from_norm or to_code != to_norm:
            changes_made += 1
            if from_code != from_norm:
                print(f"  Fallback key: {from_code} → {from_norm}")
            if to_code != to_norm:
                print(f"  Fallback val: {to_code} → {to_norm}")

        return f"{indent}{q}{from_norm}{q}: {vq}{to_norm}{vq},{comment}"

    content = re.sub(
        r"(\s+)(['\"])([a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?(?:-[a-zA-Z]{2})?)\2:\s*(['\"])([a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?(?:-[a-zA-Z]{2})?)\4,([\s]*//.*)?",
        replace_fallback,
        content
    )

    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Normalized {changes_made} language codes in {filepath}")
        return True
    else:
        print(f"  No changes needed")
        return False


def normalize_build_py(filepath):
    """Normalize language codes in build.py to proper BCP 47."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    changes_made = 0

    # Match quoted language codes in string literals and object keys
    def replace_code(m):
        nonlocal changes_made
        q = m.group(1)
        code = m.group(2)

        normalized = normalize_bcp47(code)
        if code != normalized:
            changes_made += 1
            print(f"  {code} → {normalized}")

        return f"{q}{normalized}{q}"

    content = re.sub(
        r"(['\"])([a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?(?:-[a-zA-Z]{2})?)\1",
        replace_code,
        content
    )

    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Normalized {changes_made} language codes in {filepath}")
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
        print("Normalization complete! Language codes now use proper BCP 47 casing.")
        print("   Run 'python3 build.py' to rebuild.")
    else:
        print("All language codes already use proper BCP 47 casing.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
