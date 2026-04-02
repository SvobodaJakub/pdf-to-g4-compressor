# Internationalization (i18n) Plan

This document outlines the approach for adding multi-language support to the PDF G4 Compressor.

## Design Goals

1. **Self-contained**: All translations embedded in the HTML file
2. **Simple**: Minimal JavaScript, no external libraries
3. **Automatic**: Detects browser locale, applies automatically
4. **Fallback**: Defaults to English if translation unavailable
5. **Maintainable**: Easy to add new languages

## Technical Approach

### Locale Detection

```javascript
// Detect browser locale
const userLocale = navigator.language || navigator.userLanguage; // e.g., "cs-CZ", "en-US"
const languageCode = userLocale.split('-')[0]; // e.g., "cs", "en"
```

### Translation Storage

Embed translations as JavaScript object:

```javascript
const translations = {
    en: {
        title: "PDF Monochrome CCITT G4 Compressor",
        subtitle: "Compress PDFs by reducing colors to bilevel monochrome...",
        chooseFile: "Choose PDF File",
        convert: "Compress to CCITT G4",
        // ... all UI strings
    },
    cs: {
        title: "PDF Monochromatický CCITT G4 Kompresor",
        subtitle: "Komprimujte PDF snížením barev na jednobitovou černobílou...",
        chooseFile: "Vybrat PDF soubor",
        convert: "Komprimovat do CCITT G4",
        // ... all UI strings
    },
    de: {
        title: "PDF Monochrom CCITT G4 Kompressor",
        subtitle: "PDFs komprimieren durch Reduzierung auf Schwarzweiß...",
        chooseFile: "PDF-Datei wählen",
        convert: "Zu CCITT G4 komprimieren",
        // ... all UI strings
    },
    // Add more languages as needed
};
```

### Translation Application

Mark translatable elements with data attributes:

```html
<h1 data-i18n="title">PDF Monochrome CCITT G4 Compressor</h1>
<p data-i18n="subtitle" class="subtitle">Compress PDFs...</p>
<label for="pdfFile" data-i18n="chooseFile">Choose PDF File</label>
<button id="convertBtn" data-i18n="convert">Compress to CCITT G4</button>
```

Apply translations on load:

```javascript
function applyTranslations(languageCode) {
    // Default to English
    const lang = translations[languageCode] || translations['en'];
    
    // Find all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (lang[key]) {
            element.textContent = lang[key];
        }
    });
}

// On page load
document.addEventListener('DOMContentLoaded', function() {
    const userLocale = navigator.language || 'en';
    const languageCode = userLocale.split('-')[0];
    applyTranslations(languageCode);
    
    // Continue with rest of initialization...
});
```

## Implementation Strategy

### Phase 1: Basic Structure
1. Add translation object with English and Czech
2. Mark all UI text with `data-i18n` attributes
3. Implement locale detection and application
4. Test with browser language settings

### Phase 2: Complete Translations
1. Extract all UI strings to translation keys
2. Add Czech translations
3. Add German translations (optional)
4. Add Spanish translations (optional)

### Phase 3: Advanced Features (Optional)
1. Language selector in UI (override auto-detection)
2. Store user preference in localStorage
3. Translate modal content (license, about)
4. Translate error messages and tooltips

## Translation Keys Needed

### Main UI
- `title` - Page title
- `subtitle` - Subtitle with description
- `chooseFile` - File input label
- `filename` - Selected filename display
- `convert` - Convert button

### Options
- `conversionMode` - "Conversion Mode" label
- `noDither` - "Non-dithered (Sharp)"
- `dither` - "Dithered (Smooth)"
- `ditherSelected` - "Dither only selected pages"
- `pageRange` - Page range placeholder
- `pageRangeHint` - Page range hint text
- `outputDpi` - "Output DPI (Resolution)"
- `dpiStandard` - "Standard (310 DPI)"
- `dpiCustom` - "Custom DPI"
- `dpiHint` - DPI hint text

### Progress/Status
- `loading` - "Loading PDF..."
- `processing` - "Processing..."
- `rendering` - "Rendering page {0} of {1}"
- `compressing` - "Compressing..."
- `done` - "Done!"

### Warnings
- `lowQuality` - Low DPI warning text
- `highFilesize` - High DPI warning text
- `highCompute` - High compute warning text

### Credits/Links
- `builtWith` - "Built with PDF.js • pako • G4Enc"
- `license` - "Licensed under Apache 2.0 • View Licenses & Attributions"
- `about` - "About This Project • A Study in Questionable Decisions"

### Modals
- `licenseTitle` - "License & Attributions"
- `aboutTitle` - "About This Project"
- `sourceTitle` - "Get the source tarball in base64"
- (Plus all modal content strings)

## File Size Impact

Estimated size increase:
- Translation object (2-3 languages): ~5-10 KB uncompressed
- After gzip compression: ~1-2 KB
- Minimal impact on final file size (1.48 MB → 1.49 MB)

## PWA Manifest Localization

**Question**: Should `manifest.json` include multiple languages?

**Answer**: No, keep it simple with English.

**Why**:
- The manifest is primarily for PWA installation metadata
- Name/description shown briefly during installation only
- Most users will see the translated UI immediately after opening
- Multiple manifest files add complexity for minimal benefit

**Recommended approach**:
- Keep `manifest.json` in English (default)
- Handle all UI translations in JavaScript (as planned)
- The app content is what users interact with 99% of the time

**Alternative** (if needed later):
You could create language-specific manifests:
- `manifest.json` (English, default)
- `manifest-cs.json` (Czech)
- Serve the appropriate one based on browser locale

But this adds complexity and doesn't provide much value for a single-file app.

## Browser Support

Locale detection works in all modern browsers:
- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- IE11: ✅ (with polyfill for navigator.userLanguage)

## Testing

Test with browser language settings:
```javascript
// Chrome DevTools Console:
navigator.language = 'cs-CZ'; // Force Czech
location.reload();

// Firefox: about:config → intl.accept_languages
```

## Priority Languages

1. **English (en)** - Default, already present
2. **Czech (cs)** - User's native language
3. **German (de)** - Common in Europe
4. **Spanish (es)** - Large user base
5. **French (fr)** - Common in Europe

Start with English + Czech, add others as needed.

## Implementation Checklist

- [ ] Create translation object structure
- [ ] Add Czech translations
- [ ] Mark all UI elements with data-i18n
- [ ] Implement locale detection
- [ ] Implement translation application
- [ ] Test with Czech locale
- [ ] Add to build process
- [ ] Update documentation
- [ ] (Optional) Add language selector UI
- [ ] (Optional) Add more languages

---

**Status**: Ready to implement  
**Estimated effort**: 2-3 hours for basic implementation  
**File size impact**: +1-2 KB (negligible)
