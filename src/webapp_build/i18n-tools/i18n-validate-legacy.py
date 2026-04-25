#!/usr/bin/env python3
"""
i18n Translation Validator (Legacy Regex-based)

Validates translations using regex parsing and semantic checks.
Note: This validator uses regex and may miss some edge cases.
For authoritative validation, use i18n-validate.js instead.

Usage:
  python3 i18n-tools/i18n-validate-legacy.py     # from webapp_build
  cd i18n-tools && python3 i18n-validate-legacy.py  # from i18n-tools

Reference languages (assumed correct):
- en: English
- de: German
- cs: Czech
- sk: Slovak
- pl: Polish
- ru: Russian
"""

import os
import re
import sys

# Known-good reference translations
REFERENCE_LANGS = ['en', 'de', 'cs', 'sk', 'pl', 'ru']

# Terms that should remain in English/Latin script
PRESERVED_TERMS = ['PDF', 'DPI', 'G4', 'CCITT', 'A4', 'Letter', 'Legal', 'PDF.js', 'pako', 'G4Enc', 'Apache 2.0']

# Expected fields in every translation
REQUIRED_FIELDS = [
    'title', 'subtitle', 'privacyNotice', 'chooseFile', 'conversionMode',
    'noDither', 'dither', 'ditherSelected', 'pageRangePlaceholder', 'pageRangeHint',
    'pageSize', 'pageSizeA4Portrait', 'pageSizeA4Landscape',
    'pageSizeLetterPortrait', 'pageSizeLetterLandscape', 'pageSizeLegalPortrait',
    'outputDpi', 'dpiStandard', 'dpiCustom', 'dpiHint',
    'compressButton', 'processing', 'credits', 'license', 'about',
    'lowQualityWarning',
    'resultSaveButton', 'resultRecommendIgnore', 'resultDidntCompressWell',
    'resultBecameBigger', 'resultAppPurpose', 'resultDitheringNote', 'resultDitheringAdvice',
    'advancedTricks', 'useJBIG2Label', 'jbig2Warning',
    'preserveRotationLabel', 'metadataSection', 'includeTimestampLabel',
    'ramWarningHigh', 'ramWarningCritical',
    'jbig2DisabledMpix', 'jbig2DisabledPages', 'ramOverrideAcceptRisk',
]

# Deprecated fields that should NOT exist
DEPRECATED_FIELDS = ['outputFormat', 'dpiDimensions', 'highFilesizeWarning', 'highComputeWarning']

def extract_translations(filepath):
    """Extract all language translations from JavaScript file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find TRANSLATIONS object or ADDITIONAL_TRANSLATIONS
    translations = {}

    # Find language blocks by matching opening patterns and counting braces
    lang_header = re.compile(r'^\s*["\']?([a-z]{2}(?:-[A-Za-z]+)?)["\']?\s*:\s*\{', re.MULTILINE)

    for match in lang_header.finditer(content):
        lang_code = match.group(1)
        start = match.end()
        # Find matching closing brace by counting
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            if content[pos] == '{': depth += 1
            elif content[pos] == '}': depth -= 1
            pos += 1
        lang_block = content[start:pos - 1]

        # Extract fields from this language block
        fields = {}
        # Match: fieldName: "value" or fieldName: 'value'
        # Handle apostrophes/quotes inside values by matching quote pairs
        field_pattern = r'(\w+):\s*"([^"]*)"'  # Double-quoted strings
        field_pattern_single = r"(\w+):\s*'([^']*)'"  # Single-quoted strings (rare)

        for field_match in re.finditer(field_pattern, lang_block):
            field_name = field_match.group(1)
            field_value = field_match.group(2)
            fields[field_name] = field_value

        for field_match in re.finditer(field_pattern_single, lang_block):
            field_name = field_match.group(1)
            field_value = field_match.group(2)
            if field_name not in fields:  # Don't override double-quoted
                fields[field_name] = field_value

        translations[lang_code] = fields

    return translations

def check_missing_fields(translations):
    """Check for missing required fields."""
    issues = []

    for lang, fields in sorted(translations.items()):
        missing = [f for f in REQUIRED_FIELDS if f not in fields]
        if missing:
            issues.append(f"{lang}: Missing fields: {', '.join(missing)}")

    return issues

def check_deprecated_fields(translations):
    """Check for deprecated fields that should be removed."""
    issues = []

    for lang, fields in sorted(translations.items()):
        deprecated = [f for f in DEPRECATED_FIELDS if f in fields]
        if deprecated:
            issues.append(f"{lang}: Has deprecated fields: {', '.join(deprecated)}")

    return issues

def check_preserved_terms(translations):
    """Check if technical terms are preserved correctly."""
    issues = []

    # Get reference values for terms that should be consistent
    reference = {}
    for term in PRESERVED_TERMS:
        reference[term.lower()] = term

    for lang, fields in sorted(translations.items()):
        if lang in REFERENCE_LANGS:
            continue

        for field_name, field_value in fields.items():
            # Check if preserved terms appear in wrong form
            for term in PRESERVED_TERMS:
                # Count occurrences in reference languages
                ref_count = sum(1 for ref_lang in REFERENCE_LANGS
                               if ref_lang in translations
                               and field_name in translations[ref_lang]
                               and term in translations[ref_lang][field_name])

                if ref_count > 0:
                    # This term should appear in this field
                    if term not in field_value:
                        # Allow for variations like "PDF.js" vs "PDF.js"
                        if not any(variant in field_value for variant in [term.lower(), term.upper()]):
                            issues.append(f"{lang}.{field_name}: Missing expected term '{term}'")

    return issues

def check_landscape_orientation(translations):
    """Check if 'landscape' is translated as orientation (not vista/scenery)."""
    issues = []

    # Get reference translations for landscape
    ref_landscape = {}
    for lang in REFERENCE_LANGS:
        if lang in translations and 'pageSizeA4Landscape' in translations[lang]:
            ref_landscape[lang] = translations[lang]['pageSizeA4Landscape']

    print("\nReference landscape translations:")
    for lang, value in ref_landscape.items():
        print(f"  {lang}: {value}")

    # Known problematic terms (vista/scenery meanings)
    vista_terms = {
        'krajobraz', 'pejzaž', 'пейзаж', 'peizazh', 'peisaj', 'ainava',
        'landscape', 'paisagem', 'paisaje', 'paesaggio'  # Only problematic if not in expected context
    }

    for lang, fields in sorted(translations.items()):
        if lang in REFERENCE_LANGS:
            continue

        if 'pageSizeA4Landscape' in fields:
            value = fields['pageSizeA4Landscape'].lower()

            # Check for problematic vista terms
            for vista_term in vista_terms:
                if vista_term in value and 'a4' in value.lower():
                    # Likely using vista meaning instead of orientation
                    # Check if portrait uses upright/vertical
                    portrait = fields.get('pageSizeA4Portrait', '').lower()

                    # If portrait suggests orientation (vertical/upright), landscape should too
                    orientation_indicators = ['vertical', 'horizontal', 'patayo', 'pahiga',
                                             'вертикально', 'горизонтально', 'uspravno', 'položeno']

                    has_orientation = any(ind in portrait or ind in value for ind in orientation_indicators)

                    if not has_orientation:
                        issues.append(f"{lang}.pageSizeA4Landscape: Possibly uses vista meaning ('{fields['pageSizeA4Landscape']}')")

    return issues

def check_script_consistency(translations):
    """Check if language uses consistent writing system."""
    issues = []

    # Expected scripts for language families
    SCRIPTS = {
        'ar': 'Arabic',
        'he': 'Hebrew',
        'ur': 'Arabic',
        'hi': 'Devanagari',
        'bn': 'Bengali',
        'ta': 'Tamil',
        'te': 'Telugu',
        'mr': 'Devanagari',
        'gu': 'Gujarati',
        'pa': 'Gurmukhi',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'si': 'Sinhala',
        'th': 'Thai',
        'ka': 'Georgian',
        'hy': 'Armenian',
        'am': 'Ethiopic',
        'bo': 'Tibetan',
        'my': 'Myanmar',
        'km': 'Khmer',
        'lo': 'Lao',
        'zh-Hans': 'Han',
        'zh-Hant': 'Han',
        'ja': 'Japanese',
        'ko': 'Hangul',
        'yi': 'Hebrew',
        'ru': 'Cyrillic',
        'uk': 'Cyrillic',
        'bg': 'Cyrillic',
        'sr-Cyrl': 'Cyrillic',
        'sr-Latn': 'Latin',
        'be': 'Cyrillic',
        'mk': 'Cyrillic',
        'mn': 'Cyrillic',
        'kk': 'Cyrillic',
        'uz': 'Latin',
        'az': 'Latin',
    }

    # Unicode ranges for scripts
    def detect_script(text):
        """Detect predominant script in text."""
        scripts = {
            'Arabic': 0,
            'Cyrillic': 0,
            'Devanagari': 0,
            'Bengali': 0,
            'Tamil': 0,
            'Telugu': 0,
            'Gujarati': 0,
            'Gurmukhi': 0,
            'Kannada': 0,
            'Malayalam': 0,
            'Hebrew': 0,
            'Thai': 0,
            'Georgian': 0,
            'Armenian': 0,
            'Ethiopic': 0,
            'Tibetan': 0,
            'Myanmar': 0,
            'Khmer': 0,
            'Lao': 0,
            'Han': 0,
            'Hangul': 0,
            'Japanese': 0,
            'Sinhala': 0,
            'Latin': 0,
        }

        for char in text:
            code = ord(char)
            if 0x0600 <= code <= 0x06FF: scripts['Arabic'] += 1
            elif 0x0400 <= code <= 0x04FF: scripts['Cyrillic'] += 1
            elif 0x0900 <= code <= 0x097F: scripts['Devanagari'] += 1
            elif 0x0980 <= code <= 0x09FF: scripts['Bengali'] += 1
            elif 0x0B80 <= code <= 0x0BFF: scripts['Tamil'] += 1
            elif 0x0C00 <= code <= 0x0C7F: scripts['Telugu'] += 1
            elif 0x0A80 <= code <= 0x0AFF: scripts['Gujarati'] += 1
            elif 0x0A00 <= code <= 0x0A7F: scripts['Gurmukhi'] += 1
            elif 0x0C80 <= code <= 0x0CFF: scripts['Kannada'] += 1
            elif 0x0D00 <= code <= 0x0D7F: scripts['Malayalam'] += 1
            elif 0x0590 <= code <= 0x05FF: scripts['Hebrew'] += 1
            elif 0x0E00 <= code <= 0x0E7F: scripts['Thai'] += 1
            elif 0x10A0 <= code <= 0x10FF: scripts['Georgian'] += 1
            elif 0x0530 <= code <= 0x058F: scripts['Armenian'] += 1
            elif 0x1200 <= code <= 0x137F: scripts['Ethiopic'] += 1
            elif 0x0F00 <= code <= 0x0FFF: scripts['Tibetan'] += 1
            elif 0x1000 <= code <= 0x109F: scripts['Myanmar'] += 1
            elif 0x1780 <= code <= 0x17FF: scripts['Khmer'] += 1
            elif 0x0E80 <= code <= 0x0EFF: scripts['Lao'] += 1
            elif 0x4E00 <= code <= 0x9FFF: scripts['Han'] += 1
            elif 0xAC00 <= code <= 0xD7AF: scripts['Hangul'] += 1
            elif 0x3040 <= code <= 0x30FF: scripts['Japanese'] += 1
            elif 0x0D80 <= code <= 0x0DFF: scripts['Sinhala'] += 1
            elif 0x0041 <= code <= 0x007A or 0x00C0 <= code <= 0x00FF: scripts['Latin'] += 1

        # Return predominant script
        return max(scripts.items(), key=lambda x: x[1])[0] if sum(scripts.values()) > 0 else 'Unknown'

    for lang, fields in sorted(translations.items()):
        expected_script = SCRIPTS.get(lang)
        if not expected_script:
            continue

        # Check a field that should be in native script
        if 'title' in fields:
            detected = detect_script(fields['title'])
            if detected != expected_script and detected != 'Latin':  # Latin is OK for terms like "PDF"
                issues.append(f"{lang}.title: Expected {expected_script} script but detected {detected} ('{fields['title']}')")

    return issues

def main():
    print("=" * 80)
    print("i18n Translation Validator (Legacy Regex Parser)")
    print("=" * 80)
    print(f"\nReference languages: {', '.join(REFERENCE_LANGS)}")
    print(f"Required fields: {len(REQUIRED_FIELDS)}")

    # Determine if we're running from i18n-tools/ or webapp_build/
    cwd = os.getcwd()
    parent_dir = '..' if os.path.basename(cwd) == 'i18n-tools' else '.'

    # Load translations from both files
    all_translations = {}

    for filename in ['i18n.js', 'i18n-languages.js']:
        filepath = os.path.join(parent_dir, filename)
        try:
            translations = extract_translations(filepath)
            all_translations.update(translations)
            print(f"\nLoaded {len(translations)} languages from {filepath}")
        except FileNotFoundError:
            print(f"Warning: {filepath} not found, skipping")

    print(f"\nTotal languages: {len(all_translations)}")
    print(f"Languages: {', '.join(sorted(all_translations.keys()))}")

    # Run validations
    all_issues = []

    print("\n" + "=" * 80)
    print("Checking for missing required fields...")
    print("=" * 80)
    issues = check_missing_fields(all_translations)
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
        all_issues.extend(issues)
    else:
        print("  ✅ All languages have required fields")

    print("\n" + "=" * 80)
    print("Checking for deprecated fields...")
    print("=" * 80)
    issues = check_deprecated_fields(all_translations)
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
        all_issues.extend(issues)
    else:
        print("  ✅ No deprecated fields found")

    print("\n" + "=" * 80)
    print("Checking landscape/orientation translations...")
    print("=" * 80)
    issues = check_landscape_orientation(all_translations)
    if issues:
        for issue in issues:
            print(f"  ⚠️  {issue}")
        all_issues.extend(issues)
    else:
        print("  ✅ Landscape translations look correct")

    print("\n" + "=" * 80)
    print("Checking script consistency...")
    print("=" * 80)
    issues = check_script_consistency(all_translations)
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
        all_issues.extend(issues)
    else:
        print("  ✅ All languages use correct scripts")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total issues found: {len(all_issues)}")

    if all_issues:
        print("\n❌ Validation FAILED - issues need to be fixed")
        return 1
    else:
        print("\n✅ All validations PASSED")
        return 0

if __name__ == '__main__':
    sys.exit(main())
