# Traditional Mongolian Script Implementation

## Overview
This document describes the implementation of traditional Mongolian script support in the PDF G4 Compressor web application.

## What Was Implemented

### 1. Font Integration
- **Font**: Noto Sans Mongolian (Regular)
- **License**: SIL Open Font License 1.1 (OFL 1.1)
- **Source**: https://github.com/notofonts/mongolian
- **Format**: OTF (302 KB), embedded as base64 in HTML
- **File**: `src/webapp_build/NotoSansMongolian-Regular.otf`

### 2. CSS Implementation
Added CSS support for traditional Mongolian vertical writing mode in `template.html`:

```css
/* Traditional Mongolian script support */
body.mongolian-script {
    writing-mode: vertical-lr;
    text-orientation: sideways;
    font-family: 'Noto Sans Mongolian', serif;
}
body.mongolian-script .container {
    max-width: none;
    max-height: 600px;
    height: 100vh;
    width: auto;
}
```

### 3. Translations
Added complete traditional Mongolian script translations:
- **Language code**: `mn-Mong` (traditional script) vs `mn` (Cyrillic script)
- **Script**: Traditional Mongolian script (Unicode U+1800–U+18AF)
- **Location**: `i18n-languages.js`
- **All 35 required fields** translated with technical terms preserved in Latin

### 4. Build Process Updates
Modified `build.py` to:
- Read and base64-encode the Mongolian font
- Replace `{{MONGOLIAN_FONT_BASE64}}` placeholder in template
- Include font data in final HTML build

### 5. Language Detection & Switching
Added JavaScript logic to handle Mongolian script:
- Detects `mn-Mong` language code
- Applies `mongolian-script` CSS class to `<body>`
- Removes class when switching to other languages
- Integrated with language selector modal
- Works with "Use English" checkbox

### 6. License Updates
Updated all license files:
- **LICENSES.md**: Added complete SIL OFL 1.1 license text for Noto Sans Mongolian
- **template.html**: Added Mongolian font attribution in license modal
- **README.md**: Added to third-party components list

## How It Works

### Technical Approach
Unlike Android which requires font mirroring + transformations, modern web browsers natively support Mongolian vertical writing:

1. **CSS writing-mode: vertical-lr** - Core property for top-to-bottom, left-to-right layout
2. **text-orientation: sideways** - Safari/WebKit compatibility fix
3. **Noto Sans Mongolian font** - Proper glyph rendering

### User Experience
When `mn-Mong` language is selected:
1. Page layout rotates to vertical writing mode
2. Text flows top-to-bottom in columns
3. Columns progress left-to-right
4. Font automatically switches to Noto Sans Mongolian
5. All UI elements adapt to vertical layout

## Browser Compatibility
- **Chrome**: 48+ ✅
- **Firefox**: 41+ ✅
- **Safari**: 5.1+ ✅
- **Edge**: 12+ ✅
- **Global coverage**: 97% (baseline since 2019)

## File Size Impact
- **Font size**: 302 KB (uncompressed)
- **Base64 encoded**: 403 KB
- **Impact on final HTML**: +300 KB raw, compressed in final build
- **Final build**: 2.14 MB (was ~1.9 MB)

## Testing
Run validation:
```bash
cd src/webapp_build
node i18n-tools/i18n-validate.js
```

Expected: mn-Mong should have all 35 required fields with no errors.

## Language Codes
- **mn**: Modern Mongolian (Cyrillic script) - for Mongolia
- **mn-Mong**: Traditional Mongolian (Mongolian script) - for Inner Mongolia, China

## References
- W3C Mongolian Layout Requirements: https://w3c.github.io/mlreq/
- Unicode Mongolian Block: U+1800–U+18AF
- Noto Fonts Project: https://github.com/notofonts
- SIL Open Font License: https://openfontlicense.org/
