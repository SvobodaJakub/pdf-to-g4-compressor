# Internationalization (i18n)

The application supports **83 languages** with complete translations.

## Quick Start

### Validate Translations
```bash
# Run all validators (recommended)
./i18n-tools/validate-all.sh

# Or run individually:
node i18n-tools/i18n-validate.js              # Structural validation
python3 i18n-tools/i18n-validate-legacy.py    # Semantic validation
```

### Add a New Language
1. Edit `i18n-languages.js` and add your language block with all 28 required fields
2. Run validation: `./i18n-tools/validate-all.sh`
3. Fix any errors
4. Rebuild: `python3 build.py`

### Translation Files
- **`i18n.js`** - Core 6 languages (en, de, es, pt, cs, sk)
- **`i18n-languages.js`** - Extended 77 languages (ar, zh, ja, ko, ru, etc.)

## Languages Supported

### Core Languages (6)
English, German, Spanish, Portuguese, Czech, Slovak

### Extended Languages (77)
**European:** Bulgarian, Croatian, Danish, Dutch, Estonian, Finnish, French, Greek, Hungarian, Icelandic, Italian, Latvian, Lithuanian, Macedonian, Norwegian (Bokmål & Nynorsk), Polish, Romanian, Russian, Serbian (Cyrillic & Latin), Slovenian, Swedish, Ukrainian, Albanian, Bosnian, Afrikaans, Catalan, Basque, Galician, Belarusian, Yiddish, Tatar

**Asian:** Arabic, Hebrew, Urdu, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Punjabi, Kannada, Malayalam, Oriya, Sinhala, Nepali, Assamese, Japanese, Korean, Chinese (Simplified & Traditional), Vietnamese, Thai, Indonesian, Malay, Javanese, Tagalog, Mongolian, Azerbaijani, Uzbek, Kazakh, Kyrgyz, Tajik, Turkmen, Georgian, Armenian, Persian/Farsi, Khmer, Lao, Burmese, Tibetan

**African:** Amharic, Swahili, Zulu

**Total:** 83 languages

## Features

### Auto-Detection
- Uses browser's language preferences (`navigator.languages`)
- Smart fallback: exact locale → regional fallback → base language → English
- No user interaction needed

### RTL Support
Right-to-left layout for: **Arabic, Hebrew, Urdu, Yiddish**

### Regional Variants
Supports 60+ regional locale codes with intelligent fallback:

**Examples:**
- Chinese: `zh-CN`, `zh-TW`, `zh-Hans`, `zh-Hant`
- Spanish: `es-ES`, `es-MX`, `es-AR`, `es-CO`
- German: `de-DE`, `de-AT`, `de-CH`
- English: `en-US`, `en-GB`, `en-AU`
- Serbian: `sr-Cyrl` (Cyrillic), `sr-Latn` (Latin)
- Norwegian: `nb-NO` (Bokmål), `nn-NO` (Nynorsk)

See `i18n.js` → `LOCALE_FALLBACK` for complete mapping.

## Translation Quality

**⚠️ AI-Generated**: Translations are AI-generated and validated through:
- Structural checks (all fields present)
- Semantic checks (correct terminology)
- Script consistency (writing systems)
- Cross-reference with reference languages

**Reference languages** (used for validation):
- English, German, Czech, Slovak, Polish, Russian

**Native speaker review recommended** for production use.

## File Size Impact

| Component | Size |
|-----------|------|
| i18n.js | 18 KB |
| i18n-languages.js | 192 KB |
| Total uncompressed | 210 KB |
| Compressed in HTML | ~20 KB |
| Overall increase | ~6% |

## Validation Status

✅ **All 83 languages complete** - Every language has all 28 required fields  
✅ **No deprecated fields** - All legacy fields removed  
✅ **No structural errors** - Valid JavaScript syntax  
✅ **Semantic checks pass** - Correct terminology and writing systems  

## Required Fields (28 total)

Every language must have exactly 28 fields:

### Core (7)
`title`, `subtitle`, `privacyNotice`, `chooseFile`, `conversionMode`, `processing`, `compressButton`

### Dithering (3)
`noDither`, `dither`, `ditherSelected`

### Page Range (2)
`pageRangePlaceholder`, `pageRangeHint`

### Page Size (6)
`pageSize`, `pageSizeA4Portrait`, `pageSizeA4Landscape`, `pageSizeLetterPortrait`, `pageSizeLetterLandscape`, `pageSizeLegalPortrait`

### DPI Settings (4)
`outputDpi`, `dpiStandard`, `dpiCustom`, `dpiHint`

### Credits (3)
`credits`, `license`, `about`

### Warnings (3)
`lowQualityWarning`, `highFilesizeWarning`, `highComputeWarning`

## Validation Tools

All tools are in `i18n-tools/`:

- **`i18n-validate.js`** - Primary validator using JavaScript parser (authoritative)
- **`i18n-validate-legacy.py`** - Secondary validator with semantic checks
- **`validate-all.sh`** - Runs both validators
- **`README.md`** - Complete documentation with troubleshooting

## Usage

### Testing Different Languages

**Chrome DevTools:**
```javascript
navigator.language = 'ja';  // Japanese
location.reload();
```

**Firefox:** `about:config` → `intl.accept_languages`

**Android:** Settings → Languages → Move language to top

### Before Committing
```bash
./i18n-tools/validate-all.sh  # Must pass
python3 build.py              # Rebuild HTML
```

## Technical Notes

### Language Code Format

**Standard (unquoted):**
```javascript
en: { ... },
de: { ... },
```

**Hyphenated (quoted):**
```javascript
"zh-Hans": { ... },  // Simplified Chinese
"sr-Cyrl": { ... },  // Serbian Cyrillic
```

**Reserved keywords (quoted):**
```javascript
"as": { ... },  // Assamese (as is JS keyword)
```

### Deprecated Fields

These must NOT appear:
- `outputFormat` - removed
- `dpiDimensions` - removed

### Locale Detection Logic
```javascript
// Uses full language preferences
const languages = navigator.languages || [navigator.language];

// Fallback chain:
// 1. Exact match (e.g., "de-AT")
// 2. Mapped fallback (LOCALE_FALLBACK)
// 3. Base language (e.g., "de-AT" → "de")
// 4. English default
```

## Documentation

- **This file** - Quick reference
- **`i18n-tools/README.md`** - Complete validation documentation
- **`i18n.js`** - Implementation with LOCALE_FALLBACK mapping
- **`i18n-languages.js`** - All extended translations

## Known Limitations

- Modals (license, about) remain in English (technical/legal content)
- Error messages remain in English (debugging)
- No manual language selector (auto-detect only)

## Contributing

Contributions welcome for:
- Native speaker reviews
- Translation corrections
- New languages
- Regional variants

Run validators before submitting.
