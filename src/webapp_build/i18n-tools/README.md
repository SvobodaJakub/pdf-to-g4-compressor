# i18n Translation Tools

Tools for validating and maintaining internationalization (i18n) translations for the PDF G4 Compressor application.

## Files

### Translation Files (in parent directory)
- `../i18n.js` - Core translations (6 languages: en, de, es, pt, cs, sk)
- `../i18n-languages.js` - Extended translations (77 additional languages)

**Total: 83 languages** with 28 required fields each.

### Validation Tools

#### `i18n-validate.js` (Recommended)
**Authoritative validator** - Uses proper JavaScript parsing via `eval()`.

**Features:**
- ✅ Parses actual JavaScript objects (not regex)
- ✅ Detects duplicate keys
- ✅ Validates all required fields present
- ✅ Checks for deprecated fields
- ✅ Detects empty string values
- ✅ Validates data types

**Usage:**
```bash
# From webapp_build directory:
node i18n-tools/i18n-validate.js

# Or from i18n-tools directory:
cd i18n-tools
node i18n-validate.js
```

**Exit codes:**
- `0` - All validations passed
- `1` - Validation errors found

#### `i18n-validate-legacy.py` (Secondary)
**Legacy validator** - Uses regex-based parsing with semantic checks.

**Features:**
- ✅ Checks missing/deprecated fields
- ✅ Validates "landscape" orientation vs vista meaning
- ✅ Checks script consistency (Cyrillic, Devanagari, etc.)
- ⚠️  May miss some edge cases (uses regex, not proper parsing)

**Usage:**
```bash
# From webapp_build directory:
python3 i18n-tools/i18n-validate-legacy.py

# Or from i18n-tools directory:
cd i18n-tools
python3 i18n-validate-legacy.py
```

**Reference languages** (assumed correct for semantic validation):
- `en` - English
- `de` - German
- `cs` - Czech
- `sk` - Slovak
- `pl` - Polish
- `ru` - Russian

## Required Fields

Every language must have exactly 28 fields:

### Core Fields (7)
- `title` - Application title
- `subtitle` - Application description
- `privacyNotice` - Privacy/offline notice
- `chooseFile` - File picker button text
- `conversionMode` - Conversion mode label
- `processing` - Processing status text
- `compressButton` - Main compress button text

### Dithering Options (3)
- `noDither` - Sharp/non-dithered option
- `dither` - Smooth/dithered option
- `ditherSelected` - Selective dithering option

### Page Range (2)
- `pageRangePlaceholder` - Example: "1, 3-5, 8"
- `pageRangeHint` - Instruction text

### Page Size (6)
- `pageSize` - Page size label
- `pageSizeA4Portrait` - A4 portrait option
- `pageSizeA4Landscape` - A4 landscape option
- `pageSizeLetterPortrait` - Letter portrait
- `pageSizeLetterLandscape` - Letter landscape
- `pageSizeLegalPortrait` - US Legal portrait

### DPI Settings (4)
- `outputDpi` - DPI label
- `dpiStandard` - Standard 310 DPI option
- `dpiCustom` - Custom DPI option
- `dpiHint` - DPI explanation text

### Credits & About (3)
- `credits` - Built with credits
- `license` - License text
- `about` - About link text

### Warnings (3)
- `lowQualityWarning` - Warning about low DPI
- `highFilesizeWarning` - Warning about large files
- `highComputeWarning` - Warning about high DPI processing

## Deprecated Fields

These fields should **NOT** appear in any translation:
- `outputFormat` - Removed (replaced with pageSize options)
- `dpiDimensions` - Removed (redundant with dpiHint)

## Language Code Format

### Standard Format
Most languages use simple 2-letter ISO codes:
```javascript
en: { ... },
de: { ... },
fr: { ... },
```

### Hyphenated Codes (must be quoted)
Script variants and regional codes with hyphens:
```javascript
"zh-Hans": { ... },  // Simplified Chinese
"zh-Hant": { ... },  // Traditional Chinese
"sr-Cyrl": { ... },  // Serbian Cyrillic
"sr-Latn": { ... },  // Serbian Latin
```

### Reserved Keywords (must be quoted)
```javascript
"as": { ... },  // Assamese (as is reserved in JS)
```

## Adding a New Language

1. Add the language block to `i18n-languages.js`:
```javascript
// Language Name
langCode: {
    title: "...",
    subtitle: "...",
    // ... all 28 required fields
},
```

2. Run validation:
```bash
node i18n-tools/i18n-validate.js
```

3. Fix any errors reported

4. Rebuild the application:
```bash
python3 build.py
```

## Common Validation Errors

### Missing Fields
**Error:** `langCode: Missing N fields: field1, field2`

**Fix:** Add the missing fields to the language block.

### Duplicate Keys
**Error:** `langCode: Duplicate keys: fieldName(x2)`

**Fix:** Remove duplicate field definitions (JavaScript objects silently use the last value).

### Deprecated Fields
**Error:** `langCode: Has deprecated fields: outputFormat`

**Fix:** Remove the deprecated field from the language block.

### Empty Values
**Error:** `langCode.fieldName: Empty string value`

**Fix:** Provide a translation for the field (don't leave empty strings).

## Maintenance

### Before Committing Changes
Always run validation:
```bash
node i18n-tools/i18n-validate.js
```

### After Adding Translations
1. Validate
2. Rebuild: `python3 build.py`
3. Test in browser with the new language

### Checking Semantic Issues
Use the legacy validator for advanced checks:
```bash
python3 i18n-tools/i18n-validate-legacy.py
```

This checks for issues like:
- Wrong "landscape" translation (vista vs orientation)
- Incorrect writing system (e.g., Cyrillic text in Latin-script language)

## Technical Notes

### Why Two Validators?

**JavaScript validator (`i18n-validate.js`)**
- **Pros:** Authoritative, uses proper parsing, no false positives
- **Cons:** Doesn't check semantic/linguistic issues

**Python validator (`i18n-validate-legacy.py`)**
- **Pros:** Checks semantic issues, writing systems, terminology
- **Cons:** Uses regex, can have false positives on edge cases

**Best practice:** Run both for comprehensive validation.

### File Structure

The translations are split into two files for maintainability:
- `i18n.js` - 6 core languages (heavily tested)
- `i18n-languages.js` - 77 additional languages

They are merged during the build process in `build.py`.

### Language Detection

The application auto-detects the user's language from:
1. `navigator.languages` array (preferred)
2. `navigator.language` (fallback)
3. Locale fallback map (e.g., `en-US` → `en`)
4. Base language (e.g., `pt-BR` → `pt`)
5. Default to English if no match

### RTL Languages

Right-to-left languages are automatically detected:
- `ar` - Arabic
- `he` - Hebrew
- `ur` - Urdu
- `yi` - Yiddish

The `dir="rtl"` attribute is set automatically for these languages.

## License

Same as parent project (Apache 2.0).
