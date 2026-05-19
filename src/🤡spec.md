# PDF Monochrome CCITT G4 Compressor — Complete Specification

Version: 1.2.8 (versionCode 18)
Copyright: 2026 PDF Monochrome CCITT G4 Compressor Contributors
License: Apache License 2.0
Repository: https://github.com/SvobodaJakub/pdf-to-g4-compressor
Package: com.svobodajakub.pdfg4compressor

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Distribution Formats](#2-distribution-formats)
3. [Build System](#3-build-system)
4. [Source Directory Structure](#4-source-directory-structure)
5. [Web Application Architecture](#5-web-application-architecture)
6. [HTML Template (template.html)](#6-html-template)
7. [JavaScript Modules](#7-javascript-modules)
8. [Internationalization (i18n)](#8-internationalization)
9. [Image Processing Pipeline](#9-image-processing-pipeline)
10. [CCITT Group 4 Encoder (g4enc.js)](#10-ccitt-group-4-encoder)
11. [JBIG2 Compression System](#11-jbig2-compression-system)
12. [PDF Generation](#12-pdf-generation)
13. [PDF Stream Compressor (pdfcompress.js)](#13-pdf-stream-compressor)
14. [ZIP Processing](#14-zip-processing)
15. [State Machine](#15-state-machine)
16. [Memory Management](#16-memory-management)
17. [AI Auto-Setter](#17-ai-auto-setter)
18. [Intro Animation](#18-intro-animation)
19. [Easter Eggs and Humor](#19-easter-eggs-and-humor)
20. [Android Wrapper (build-apk.sh)](#20-android-wrapper)
21. [Memory Probe System](#21-memory-probe-system)
22. [Android File Handling](#22-android-file-handling)
23. [State Preservation Across WebView Kills](#23-state-preservation-across-webview-kills)
24. [Self-Extracting HTML Loader](#24-self-extracting-html-loader)
25. [Self-Download Feature](#25-self-download-feature)
26. [Dark Mode](#26-dark-mode)
27. [Accessibility](#27-accessibility)
28. [Privacy](#28-privacy)
29. [Third-Party Components and Licensing](#29-third-party-components-and-licensing)
30. [Python CLI Tools](#30-python-cli-tools)
31. [Shell Example Scripts](#31-shell-example-scripts)
32. [WASM Build System](#32-wasm-build-system)
33. [i18n Validation Tools](#33-i18n-validation-tools)
34. [Pitfalls, Gotchas, and Non-Obvious Behaviors](#34-pitfalls-gotchas-and-non-obvious-behaviors)
35. [Testing Procedures](#35-testing-procedures)
36. [Android Locale Resource Generation](#36-android-locale-resource-generation)
37. [Android Emulator and Screenshot Automation](#37-android-emulator-and-screenshot-automation)
38. [Input Hint Box](#38-input-hint-box)
39. [Page Count Limit](#39-page-count-limit)
40. [JBIG2 PDF File Format Details](#40-jbig2-pdf-file-format-details)
41. [GitHub Corner Visibility](#41-github-corner-visibility)
42. [Flat Earth Animation Technical Details](#42-flat-earth-animation-technical-details)
43. [Rendering Pipeline Details](#43-rendering-pipeline-details)
44. [Result Box Color Coding](#44-result-box-color-coding)
45. [Architecture Decision: Why Pure JavaScript](#45-architecture-decision-why-pure-javascript)
46. [Detailed Algorithm Specifications](#46-detailed-algorithm-specifications)
47. [Code Wiring and Control Flow](#47-code-wiring-and-control-flow)

---

## 1. Product Overview

This application compresses PDF files by converting each page to a bilevel (1-bit black-and-white) raster image and re-encoding it with CCITT Group 4 (lossless) or JBIG2 (lossy with symbol matching) compression. The output is a PDF/A-1B compliant file.

It is designed for scanned paper documents. It is not designed for PDFs containing copiable text, vector graphics, or already-compressed scanned content.

The application exists in two forms:

1. A single self-contained HTML file (~2.7 MB) that runs entirely offline in any modern browser.
2. An Android APK/AAB that wraps the same HTML file in a WebView with native file handling.

Both forms require zero network access. The Android manifest declares no internet permission.

Typical compression results: 10-80 KB per text page (CCITT G4), 5-50 KB per text page (JBIG2 at threshold 0.97).

---

## 2. Distribution Formats

### 2.1 HTML File

Filename: `pdf-to-g4-compressor.html`

The HTML file is a self-extracting loader. It contains:
- A minimal loader HTML page with a spinner and the pako library.
- The full application HTML, gzip-compressed with zlib level 9 and base64-encoded.

On load, the loader decompresses the payload using pako, clears the document, and writes the decompressed HTML via `document.write()`. Before clearing, it saves a pristine copy of itself (the loader HTML) to `window.PRISTINE_HTML` for the self-download feature.

The full (decompressed) application HTML contains all JavaScript inlined, all CSS inlined, the Noto Sans Mongolian font as a base64-encoded @font-face, the jbig2.wasm binary as base64, the PDF.js worker as base64, and a complete source code tarball (tar.xz) as base64.

The file has no external dependencies. It makes no network requests. It works when opened from a local filesystem via `file://` protocol.

To extract the embedded source code: open the app in a browser, click "Licensed under Apache 2.0", scroll to "Get the source tarball in base64", copy the base64 text or download as .txt, then:
```
base64 -d source-base64.txt > source.tar.xz
tar -xJf source.tar.xz
```
Rebuilding from extracted source produces a byte-for-byte identical HTML file.

### 2.2 Android APK/AAB

Package name: `com.svobodajakub.pdfg4compressor`
Min SDK: 21 (Android 5.0)
Target SDK: 35 (Android 15)

The APK contains the same HTML file as `assets/index.html`, loaded in a WebView. The Java wrapper provides:
- Native file picker (ACTION_OPEN_DOCUMENT) and save dialog (ACTION_CREATE_DOCUMENT)
- Memory tier detection via a calibration probe on first launch
- State preservation across WebView kills
- Modal state tracking for Android back button
- Screen-on flag during processing

---

## 3. Build System

### 3.1 HTML Build (build.py)

Working directory: `src/webapp_build/`
Command: `python build.py`
Output: `../../pdf-to-g4-compressor.html` (relative to webapp_build/)

The script:
1. Reads all JavaScript modules from `webapp_build/`.
2. Reads PDF.js legacy builds from `libs/`.
3. Reads the jbig2.wasm binary and its JS loader from `wasm/`.
4. Reads the Noto Sans Mongolian font.
5. Reads the SVG path data for the Flat Earth background from `flatearth-paths.json` and injects them into `flatearth.js`. In `flatearth.js`, the continent paths are declared as:
   ```javascript
   var FE_LAND_PATHS = [FLATEARTH_PATHS_PLACEHOLDER];
   ```
   build.py loads the JSON file (an array of 121 SVG path `d`-attribute strings), joins them into a comma-separated list of double-quoted strings, and replaces the bare token `FLATEARTH_PATHS_PLACEHOLDER` (without the surrounding brackets — those are already in the source file):
   ```python
   _fe_paths = json.load(open('flatearth-paths.json'))
   _fe_paths_str = ','.join('"' + p + '"' for p in _fe_paths)
   flatearth_js = flatearth_js_raw.replace('FLATEARTH_PATHS_PLACEHOLDER', _fe_paths_str)
   ```
   The resulting JavaScript after replacement is `var FE_LAND_PATHS = ["M 50 10 L...", "M 30 20 L...", ...];`. Note that the path strings are not escaped via `json.dumps()` — they are wrapped in plain double quotes with `'"' + p + '"'`. This works because the SVG path data contains only digits, letters, spaces, and periods (no characters that would need escaping).

6. Merges `i18n.js` (core translations for en, de, es, pt, cs, sk) with `i18n-languages.js` (all remaining languages). The merge is a two-step text manipulation:

   **Step 6a — Extract additional translations**: build.py reads `i18n-languages.js` which declares `const ADDITIONAL_TRANSLATIONS = { hu: {...}, fr: {...}, ... };`. The inner content is extracted with:
   ```python
   match = re.search(r'const ADDITIONAL_TRANSLATIONS = \{(.*)\};', i18n_languages, re.DOTALL)
   additional_langs = match.group(1)
   ```
   `group(1)` captures only the content between the outer `{` and `};` — NOT including the braces themselves. For example, if the file contains `const ADDITIONAL_TRANSLATIONS = { hu: {...}, fr: {...} };`, then `additional_langs` is `" hu: {...}, fr: {...} "`. Including the outer braces would produce a nested `{{ ... }}` in the merged output, which would be a syntax error.

   **Step 6b — Splice into TRANSLATIONS**: `i18n.js` ends with:
   ```javascript
       },                                          // end of last core language (sk)
   
       // Continue in next file due to length...
   };                                              // end of TRANSLATIONS object
   ```
   build.py replaces the marker comment AND the closing `};` as a single string:
   ```python
   i18n = i18n_core.replace(
       '    // Continue in next file due to length...\n};',
       additional_langs + '\n};'
   )
   ```
   The replacement target is exactly `'    // Continue in next file due to length...\n};'` — 4 leading spaces, the comment text, a newline, and `};`. The replacement is `additional_langs + '\n};'` — the extracted content (which starts with language entries like `\n    hu: {...},`) followed by a newline and the closing `};`. Because the last core language (`sk`) already has a trailing comma, no extra comma is needed before the additional content.

   If the regex in step 6a fails to match (e.g., `i18n-languages.js` is missing or malformed), build.py prints a warning and uses the core i18n file alone (6 languages only).
7. Patches the Emscripten jbig2.js loader to use `window.Module||{}` instead of `typeof Module!="undefined"?Module:{}` so that re-initialization via `new Function()` works.
8. Base64-encodes the PDF.js worker, the WASM binary, and the Mongolian font.
9. Creates a tar.xz of the entire `src/` directory (excluding the built HTML file) with maximum compression (`XZ_OPT=-9e`), then base64-encodes it.
10. Reads `template.html` and replaces `{{JAVASCRIPT}}` with the assembled JS section, `{{MONGOLIAN_FONT_BASE64}}` with the font data, and `{app_version}` with the version string read from `build-apk.sh`.
11. Passes the full HTML through `create_self_extracting_loader()` which gzip-compresses it and wraps it in the minimal loader page.
12. Writes the final file.

### 3.1.1 JavaScript Assembly Structure

The JavaScript section (`js_section`) assembled by build.py is a single Python f-string that produces the entire `<script>` block. It contains two categories of code: **external modules** read from `.js` files and injected via f-string interpolation (e.g., `{pako}`, `{g4enc}`), and **inline application code** written directly in the f-string. The inline code constitutes ~3,660 lines — the entire application logic, state machine, event handlers, AI auto-setter, language selector, modals, and DOM wiring. This code exists ONLY inside build.py, not in separate `.js` files.

Because the JavaScript is inside a Python f-string, every literal JavaScript `{` and `}` must be doubled (`{{`/`}}`). For example, `function() { ... }` in JavaScript is written as `function() {{ ... }}` in the f-string. This escaping is pervasive (~700 occurrences).

The assembled `<script>` block has this exact structure, in order:

```
<script>
├── License/copyright comment block (see section 3.1.2)         [INLINE, ~70 lines]
├── SOURCE_TARBALL_BASE64 constant                               [INLINE, data from create_source_tarball()]
├── pako (zlib) library                                          [EXTERNAL: libs/pako.min.js]
├── Merged i18n (translations + locale detection)                [EXTERNAL: i18n.js + i18n-languages.js, merged]
├── PDF.js library                                               [EXTERNAL: libs/pdf.legacy.min.js]
├── PDF.js Worker Setup IIFE (see section 3.1.3)                 [INLINE, ~17 lines, uses pdfjsworker_b64]
├── G4Enc (CCITT Group 4 encoder)                                [EXTERNAL: g4enc.js]
├── JBIG2 WASM binary decode IIFE                                [INLINE, ~12 lines, uses jbig2_wasm_b64]
├── JBIG2 loader source assignment                               [INLINE, 1 line: window._jbig2LoaderSource = <json>]
├── JBIG2 initial Module object + first-time loader execution    [INLINE, ~15 lines + EXTERNAL: wasm/jbig2.js]
├── initJBIG2Module() re-initialization function                 [INLINE, ~15 lines]
├── JBIG2 Wrapper (JBIG2Encoder class)                           [EXTERNAL: jbig2-wrapper.js]
├── JBIG2 PDF Generator                                          [EXTERNAL: jbig2pdf.js]
├── Image Processing Pipeline                                    [EXTERNAL: imageprocessing.js]
├── PDF Generation (CCITT G4)                                    [EXTERNAL: pdfgen.js]
├── PDF Compression (FlateDecode)                                [EXTERNAL: pdfcompress.js]
├── ZIP Utilities                                                [EXTERNAL: ziputil.js]
├── Intro Animation                                              [EXTERNAL: intro.js]
├── Flat Earth Background                                        [EXTERNAL: flatearth.js (with paths injected)]
├── PRISTINE_HTML fallback (see section 3.1.4)                   [INLINE, ~4 lines]
├── State machine comment block                                  [INLINE, ~77 lines, documentation only]
├── Global variables                                             [INLINE, ~45 lines]
├── defaultResultSettings() function                             [INLINE]
├── DOM element reference declarations                           [INLINE]
├── pageshow event listener (bfcache restore)                    [INLINE, ~7 lines]
├── resetAppState() function                                     [INLINE, ~150 lines]
├── DOMContentLoaded handler                                     [INLINE, ~3,370 lines]
│   ├── Initialization: locale detection, April 1st, translations, Mongolian/FE setup
│   ├── Language switch checkboxes: English, Mongolian, language selector modal
│   ├── DOM element assignment (pdfFileInput, convertBtn, etc.)
│   ├── Utility functions: updateDPIDisplay, formatFileSize, getCurrentDPI, getCurrentPageSize
│   ├── RAM estimation: estimateRAMBytes, findMaxSafeDPI, autoAdjustDPI
│   ├── File handling: loadPDFWithTimeout, countPages, detectFileType, handleFileSelected
│   ├── State management: getCurrentFormState, saveAppState, restoreAppState
│   ├── UI updates: updateCompressButton, validateControls, updateDPIWarning, updateInputHint
│   ├── Form control management: setFormControlsEnabled, cleanupPreviousResult
│   ├── Memory: deepCleanMemory
│   ├── Error handling: recoverFromError, setFileError, clearFileError, setPageRangeError, clearPageRangeError
│   ├── ZIP mode: updateZipModeUI
│   ├── File input/drop handlers, DPI radio/slider handlers, page range handler
│   ├── Compress button click handler (async, ~130 lines)
│   ├── parsePageRange function
│   ├── Conversion: convertPDF (~115 lines), convertZIP (~130 lines)
│   ├── Advanced Tricks: buildAdvancedTricksHTML (~60 lines), attachAdvancedTricksListeners (~60 lines)
│   ├── Result display: showCancelledBox, showResultBox (~135 lines)
│   ├── validateFormMatchesResult (~65 lines)
│   ├── renderPDFPages (~200 lines)
│   ├── downloadFile (~170 lines, with Android chunked save path)
│   ├── Android state restoration (hasRestoredState check, chunked file read)
│   ├── Browser form restoration detection (setTimeout 100ms)
│   ├── Intro animation start (or skip if restoring)
│   ├── Modal handlers (License, About, Privacy, Language)
│   ├── Language selector: populateLanguageList, LANGUAGE_NAMES constant, click handler
│   ├── AI Auto-Setter section (~800 lines):
│   │   ├── detectPageFormat, isJBIG2AllowableForTrial, isFormAtDefaults, resetFormToDefaults
│   │   ├── hideAIBoxes, scheduleLuckyRainbow, scheduleHappyRainbow, stopRainbowTimers
│   │   ├── createAutoSetterButton (~130 lines, with sparkles/unicorns/rainbow SVG)
│   │   ├── createRefreshBox
│   │   ├── showAutoSetterButton, showRefreshButton, showAutoSetterOrRefresh
│   │   ├── makeSaveFabulous, removeSaveFabulous
│   │   └── runAutoSetter (~440 lines, with EMA progress tracking)
│   ├── AI/refresh hide-on-interaction IIFE
│   └── Mongolian wheel scroll IIFE
</script>
```

The key architectural consequence: all functions inside the `DOMContentLoaded` handler are closures over the handler's local scope. They share access to `t` (current translations object), DOM element references, and all other local variables. Functions outside `DOMContentLoaded` (like `resetAppState()`) can only access the `var`-declared globals.

### 3.1.2 Generated License/Copyright Comment Block

The `<script>` element begins with a ~70-line block comment containing:
1. Project title: "PDF Monochrome CCITT G4 Compressor - Single-File Web Application"
2. "Generated by Claude AI"
3. Copyright notice: "Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors"
4. Full Apache 2.0 license header text (with URL)
5. "THIRD-PARTY COMPONENTS" section listing 6 components with copyright, license, and URL:
   - PDF.js (Mozilla, Apache 2.0)
   - pako (Puzrin/Tuputcyn, MIT)
   - G4Enc (BitBank/Larry Bank, Apache 2.0, "Ported from C to JavaScript")
   - jbig2enc (Google, Apache 2.0, "Compiled to WebAssembly with Emscripten")
   - Leptonica (BSD 2-Clause, "linked in jbig2enc WASM")
   - LibTIFF (LibTIFF License, "TIFFBitRevTable, used in Python source")
6. "PROJECTS STUDIED (NO CODE COPIED)" section:
   - img2pdf (Johannes Schauer Marin Rodrigues, LGPL v3+) with clean-room rationale

### 3.1.3 PDF.js Worker Base64 Embedding

build.py generates a self-contained IIFE that sets up the PDF.js worker from base64-encoded data:

```javascript
(function() {
    const workerBase64 = '<base64-encoded pdf.worker.legacy.min.js>';
    const workerBinary = atob(workerBase64);
    const workerBytes = new Uint8Array(workerBinary.length);
    for (let i = 0; i < workerBinary.length; i++) {
        workerBytes[i] = workerBinary.charCodeAt(i);
    }
    const blob = new Blob([workerBytes], { type: 'application/javascript' });
    const workerUrl = URL.createObjectURL(blob);
    pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
    console.log('PDF.js worker configured from inline code');
})();
```

The `atob()` → `charCodeAt()` loop → `Uint8Array` → `Blob` → `createObjectURL()` pattern is also used for decoding the JBIG2 WASM binary. The `String.fromCharCode` per-byte approach (used in the reverse direction for chunked save, section 47.4) avoids `Function.apply` stack overflow on large data.

### 3.1.4 PRISTINE_HTML Fallback

After the external modules and before the state machine comment, the f-string includes:

```javascript
if (typeof window.PRISTINE_HTML === 'undefined') {
    window.PRISTINE_HTML = document.documentElement.outerHTML;
}
```

This fallback fires when the application HTML is opened directly (not through the self-extracting loader). The loader normally sets `window.PRISTINE_HTML` before `document.write()` (section 24.2). Without this fallback, the self-download feature (section 25) would fail because `PRISTINE_HTML` would be undefined. The fallback captures the current DOM as HTML, which is the decompressed application — not the loader wrapper. This means a file downloaded via this fallback path would be the full uncompressed HTML (~4.2 MB), not the compressed loader (~2.7 MB). The loader path produces a byte-for-byte identical compressed copy.

### 3.1.5 Python F-String Escaping

The `js_section` variable is a Python f-string (prefix `f"""`). This means:
- `{variable_name}` performs Python string interpolation (used for `{pako}`, `{g4enc}`, etc.)
- `{{` and `}}` produce literal `{` and `}` in the output (used for all JavaScript braces)
- The template placeholders in `template.html` use `{{JAVASCRIPT}}` (double braces) because they appear inside the f-string and must survive evaluation as literal `{JAVASCRIPT}`, which is then replaced by `str.replace('{JAVASCRIPT}', js_section)`.
- The `{app_version}` placeholder in `template.html` uses single braces and is substituted via `str.replace('{app_version}', ...)` AFTER the f-string has already been evaluated (it appears in `html_template`, not in `js_section`).

The substitution order is:
1. Python evaluates the f-string `js_section`, consuming `{var}` interpolations and converting `{{`→`{`.
2. `html_template.replace('{JAVASCRIPT}', js_section)` — injects the JS into the HTML template (the `{{JAVASCRIPT}}` in the template file became `{JAVASCRIPT}` when read as a plain string, matching the replace target).
3. `.replace('{MONGOLIAN_FONT_BASE64}', ...)` — injects the font data.
4. `.replace('{app_version}', ...)` — injects the version string.

### 3.1.6 jbig2.js Patch Verification

After patching the Emscripten loader (step 7), build.py checks whether the replacement actually changed the string:

```python
if jbig2_js_reinit == jbig2_js:
    print("  WARNING: Could not patch Module detection in jbig2.js — reinit may fail")
```

If the upstream `jbig2.js` changes its Module detection pattern, this warning alerts the developer that re-initialization via `new Function()` (section 11.2) will likely break.

The version string is extracted from `build-apk.sh` by regex-matching `VERSION_NAME="..."` and prepended with `v` — e.g., `VERSION_NAME="1.2.8"` becomes `v1.2.8`. If the file is not found, an empty string is used.

### 3.2 Android Build (build-apk.sh)

Working directory: `src/`
Command: `./build-apk.sh`
Output: `../android-build/` directory with complete Gradle project

Prerequisites: JDK 17+, Android SDK, ImageMagick (for icon generation). The script checks for `java` availability and prints a Fedora-specific install hint (`sudo dnf install java-17-openjdk java-17-openjdk-devel`) if missing. It also tries `magick` first, then falls back to `convert` for ImageMagick command detection.

#### 3.2.1 Directory Variables

The script computes all paths from `BASH_SOURCE[0]` so it works regardless of the caller's working directory:

| Variable | Value | Description |
|---|---|---|
| `SCRIPT_DIR` | `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` | Directory containing `build-apk.sh` |
| `SRC_DIR` | `$SCRIPT_DIR` | Same as script dir (both are `src/`) |
| `PROJECT_ROOT` | `$(cd "$SRC_DIR/.." && pwd)` | Parent of `src/` |
| `BUILD_DIR` | `$PROJECT_ROOT/android-build` | Output Gradle project |
| `KEYSTORE_DIR` | `$PROJECT_ROOT/android-private` | Signing keys (not in git) |

#### 3.2.2 Build Directory Cleanup

If `$BUILD_DIR` already exists, the script prompts interactively:

```
⚠ Build directory exists. Clean it? (y/n)
```

If the user enters `y`, the directory is deleted with `rm -rf` and recreated. Otherwise, existing files are overwritten in-place (files not regenerated by the script remain).

#### 3.2.3 Build Steps

The script:
1. Creates the Android project directory structure under `../android-build/`.
2. Copies `pdf-to-g4-compressor.html` to `app/src/main/assets/index.html`.
3. Generates launcher icons from `icon.svg` at five density buckets using ImageMagick:

   | Density | Resolution | Mipmap directory |
   |---|---|---|
   | mdpi | 48×48 px | `mipmap-mdpi` |
   | hdpi | 72×72 px | `mipmap-hdpi` |
   | xhdpi | 96×96 px | `mipmap-xhdpi` |
   | xxhdpi | 144×144 px | `mipmap-xxhdpi` |
   | xxxhdpi | 192×192 px | `mipmap-xxxhdpi` |

   All icons are named `ic_launcher.png`. The icon depicts a thick stack of paper documents (before compression) with horizontal arrows indicating compression, a thin stack below (after compression), and a "G4" label. Purple gradient background (#667eea) matches the app UI. The icon is public domain — composed of simple geometric shapes with no copyrighted or trademarked elements. To regenerate PNGs from SVG: `magick icon.svg -resize 192x192 icon-192.png`.

4. Writes `AndroidManifest.xml` as a heredoc.
5. Writes `MainActivity.java` as a heredoc (this is the source of truth for the Java code).
6. Writes `strings.xml`, `styles.xml` (light, dark, API 35 variants), Gradle build files, and wrapper properties (see section 3.2.4).
7. Writes emulator setup scripts and screenshot automation scripts into the build directory.
8. Runs `GENERATE-ANDROID-LOCALES.py` to create locale-specific `strings.xml` files (section 36).
9. Does NOT build the APK — that requires running `./gradlew assembleRelease` and `./gradlew bundleRelease` manually in `android-build/`.

The signing keystore is expected at `../android-private/release.keystore` with properties at `../android-private/keystore.properties`. The `android-private/` directory is NOT committed to git.

#### 3.2.4 Generated Gradle and Resource Files

**`strings.xml`** (`app/src/main/res/values/strings.xml`):

```xml
<resources>
    <string name="app_name">PDF G4 Compressor</string>
    <string name="calibrating">First launch, calibrating…</string>
</resources>
```

`app_name` is the short launcher name "PDF G4 Compressor" (not the full product name "PDF Monochrome CCITT G4 Compressor" used in the HTML title). `calibrating` is shown during the memory probe on first launch (section 21.3). Both strings are translated into 73+ languages by the locale generator (section 36).

**`build.gradle`** (root, `android-build/build.gradle`):

```groovy
buildscript {
    repositories { google(); mavenCentral() }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.3.0'   // AGP version
    }
}
allprojects { repositories { google(); mavenCentral() } }
task clean(type: Delete) { delete rootProject.buildDir }
```

**`app/build.gradle`**:

- `namespace 'com.svobodajakub.pdfg4compressor'`
- `compileSdk 35`, `minSdk 21`, `targetSdk 35`
- `versionCode` and `versionName` are interpolated from shell variables `$VERSION_CODE` and `$VERSION_NAME` (this is an unquoted heredoc `APP_GRADLE_EOF`, not a single-quoted one, so shell variables are expanded).
- `minifyEnabled false` — ProGuard/R8 code shrinking is disabled. The `proguardFiles` line references the default ProGuard config but has no effect since minification is off.
- `compileOptions`: `sourceCompatibility` and `targetCompatibility` set to `JavaVersion.VERSION_17`.
- **Signing config** (conditional): If `../android-private/keystore.properties` exists, loads it via `new Properties()` + `new FileInputStream()` and creates a `signingConfigs.release` block. The `storeFile` path is resolved relative to `rootProject` with `rootProject.file("../" + keystoreProperties['storeFile'])`.
- **Dependencies**: `androidx.webkit:webkit:1.7.0`, `androidx.activity:activity:1.9.0`, `androidx.core:core:1.13.0`. Plus a constraints block forcing `org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.0` to resolve duplicate class errors from transitive dependencies.

**`settings.gradle`**:

```groovy
include ':app'
```

**`gradle.properties`**:

```properties
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
android.enableJetifier=true
```

`-Xmx2048m` gives the Gradle daemon 2 GB of heap. `useAndroidX` and `enableJetifier` are required for the AndroidX dependency migration.

**`local.properties`**: Generated with the Android SDK path. The script probes four locations in order:

1. `$HOME/Android/platform-tools` (standard user install on Linux)
2. `$ANDROID_HOME` environment variable
3. `$ANDROID_SDK_ROOT` environment variable
4. `/usr/lib/android-sdk` (system package on Debian/Ubuntu)

If found: writes `sdk.dir=<path>`. If none found: prints a warning and skips the file — the user must create it manually.

**`gradle/wrapper/gradle-wrapper.properties`**:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.7-bin.zip
```

Uses Gradle 8.7. The wrapper JAR (`gradle-wrapper.jar`), `gradlew`, and `gradlew.bat` are downloaded from the Gradle GitHub repository (`raw.githubusercontent.com/gradle/gradle/master/...`) if `gradlew` does not already exist. `gradlew` is made executable with `chmod +x`.

### 3.3 Full Rebuild Sequence

```
cd src/webapp_build/ && python build.py
cd ../.. 
cd src/ && ./build-apk.sh
cd ../android-build/ && ./gradlew assembleRelease && ./gradlew bundleRelease
```

Or the combo oneliner:
```
( cd src/webapp_build/ && python build.py ; ) && ( cd android-build/ && ./gradlew assembleRelease && ./gradlew bundleRelease ; )
```

---

## 4. Source Directory Structure

```
src/
├── build-apk.sh                  # Android APK builder (source of truth for Java)
├── icon.svg                      # Source icon (SVG, public domain, see below)
├── icon-192.png                  # PWA icon 192x192
├── icon-512.png                  # Play Store icon 512x512
├── manifest.json                 # PWA manifest (reference only — inlined in template)
├── setup-android-build.sh        # Legacy: Bubblewrap TWA setup (obsoleted by build-apk.sh)
├── privacy_policy.md             # Privacy policy (source text)
├── LICENSES.md                   # Full license texts for all components
├── 🤡spec.md                     # This file
├── ccitt_g4_pdf_compression_example.sh   # CLI example: G4 compression via GraphicsMagick
├── jbig2_pdf_compression_example.sh      # CLI example: JBIG2 compression
├── pdf_compress.py               # CLI tool: FlateDecode compress PDF streams
├── tiff2pdf_img2pdf.py           # CLI tool: CCITT G4 TIFF to PDF/A-1B
├── jbig2pdf.py                   # CLI tool: JBIG2 output to PDF/A-1B
└── webapp_build/
    ├── build.py                  # HTML build script
    ├── template.html             # HTML template (2443 lines)
    ├── g4enc.js                  # CCITT G4 encoder (ported from C)
    ├── imageprocessing.js        # Image pipeline: grayscale → normalize → levels → bilevel
    ├── pdfgen.js                 # PDF/A-1B generator for CCITT G4 images
    ├── jbig2pdf.js               # PDF/A-1B generator for JBIG2 images
    ├── jbig2-wrapper.js          # High-level JS API for jbig2enc WASM
    ├── pdfcompress.js            # FlateDecode compressor for PDF streams
    ├── ziputil.js                # Minimal ZIP reader/writer using pako
    ├── i18n.js                   # i18n core: locale detection, RTL, translation application
    ├── i18n-languages.js         # Translation strings for 60+ additional languages
    ├── intro.js                  # Intro/tutorial animation system
    ├── flatearth.js              # Flat Earth background animation (easter egg)
    ├── flatearth-paths.json      # SVG continent paths for Flat Earth background
    ├── normalize-locale-codes.py # BCP 47 locale code normalizer utility
    ├── NotoSansMongolian-Regular.otf  # Mongolian font (embedded in build)
    ├── libs/
    │   ├── pako.min.js               # zlib port (MIT)
    │   ├── pdf.legacy.min.js         # PDF.js v2.16.105 legacy build
    │   ├── pdf.worker.legacy.min.js  # PDF.js worker (legacy)
    │   ├── pdf.min.mjs               # PDF.js modern build (not used in build)
    │   └── pdf.worker.min.mjs        # PDF.js worker modern (not used in build)
    ├── wasm/
    │   ├── jbig2.wasm                # Compiled jbig2enc WebAssembly module
    │   ├── jbig2.js                  # Emscripten JS loader for WASM
    │   ├── build-jbig2-wasm.sh       # Build script for WASM from source
    │   ├── jbig2enc-emscripten.patch # Patch: replace POSIX I/O with fopen/fwrite/fclose
    │   ├── test-jbig2.html           # Minimal test harness for WASM module
    │   └── LICENSES_WASM.md          # License info for WASM components
    └── i18n-tools/
        ├── i18n-validate.js          # Structural validator (JS parsing)
        ├── i18n-validate-legacy.py   # Semantic validator (regex + script detection)
        └── validate-all.sh           # Master validation runner
```

---

## 5. Web Application Architecture

The application is a single-page app with no routing. All logic is in one `DOMContentLoaded` handler, plus globals declared above it for state that must survive `resetAppState()`.

### 5.1 Global State Variables (declared outside DOMContentLoaded)

- `currentLang`, `detectedLang` — current and OS-detected locale codes
- `selectedFile` — the File object from the file picker
- `isZipMode` — whether the selected file is a ZIP containing PDFs
- `totalPageCount`, `maxPagesPerPDF`, `inputFileSize` — file metadata
- `fileError`, `pageRangeError` — validation error flags
- `resultSettings` — object tracking all settings used for the current compression result: `{fileName, ditherMode, pageRange, dpi, pageSize, useJBIG2, jbig2Threshold, preserveRotation, includeProducer, includeTimestamp}`. Defaults: `{fileName: null, ditherMode: null, pageRange: null, dpi: null, pageSize: null, useJBIG2: false, jbig2Threshold: 0.97, preserveRotation: false, includeProducer: true, includeTimestamp: true}`
- `conversionInProgress`, `cancellationRequested` — conversion state
- `autoSetterRunning`, `autoSetterJustFinished` — AI auto-setter state
- `progressBoxState` — null, 'result', or 'cancelled'
- `_lastKnownState` — form state snapshot for restoration (survives resetAppState and bfcache)
- `resultUsedJBIG2` — whether the current result was compressed with JBIG2

### 5.2 Key Functions

| Function | Purpose |
|---|---|
| `resetAppState()` | Resets form, clears file, resets language, clears result. Does NOT clear `_lastKnownState`. |
| `saveAppState()` | Snapshots form + file into `_lastKnownState` and mirrors to Android wrapper. |
| `restoreAppState()` | Applies `_lastKnownState`: restores language, form controls, re-opens file, shows Advanced Tricks. Single code path for all restore triggers. |
| `handleFileSelected(file)` | File-open flow: detect type → count pages → auto-adjust DPI → update compress button. |
| `updateCompressButton()` | Single source of truth for compress button enable/disable, file info, JBIG2 feasibility, RAM override, DPI warning. Called on every relevant state change. |
| `convertPDF(file, ...)` | Main conversion: read file → render pages → G4/JBIG2 encode → free intermediate data (JBIG2 result sym/pages, page arrays) → FlateDecode → show result. |
| `convertZIP(file, ...)` | Batch conversion: parse ZIP → convert each PDF → create result ZIP. |
| `renderPDFPages(pdfData, ...)` | Renders PDF pages to bilevel using PDF.js + image processing pipeline. |
| `downloadFile(data, filename)` | Save result: Android path (chunked base64 to temp file) or browser path (Blob URL). |
| `deepCleanMemory()` | Aggressive pre-conversion cleanup: nulls results, zeros canvases, reinitializes JBIG2 WASM. |
| `showResultBox()` | Displays compression result with size comparison, Advanced Tricks, save button. |
| `showCancelledBox()` | Displays Advanced Tricks section only (after cancellation or file re-selection). |
| `buildAdvancedTricksHTML(expanded)` | Generates HTML for Advanced Tricks section (JBIG2 checkbox, threshold, rotation, metadata). |
| `recoverFromError()` | Error recovery: saves form state, replays handleFileSelected, restores settings. |
| `showAutoSetterOrRefresh()` | Decides whether to show AI button, refresh icon, or nothing. |
| `runAutoSetter()` | The "AI" auto-setter: tries DPI/dither/codec combinations, picks smallest result. |

---

## 6. HTML Template

File: `webapp_build/template.html` (2443 lines)

The template contains all CSS (inlined in `<style>` tags) and HTML structure. JavaScript is injected via the `{{JAVASCRIPT}}` placeholder at the end of `<body>`. The template uses two build-time placeholders: `{{JAVASCRIPT}}` (the assembled JS section), `{{MONGOLIAN_FONT_BASE64}}` (the Noto Sans Mongolian font as base64, used in a `@font-face` `src: url(data:font/otf;base64,...)` declaration), and `{app_version}` (version string, see section 3.1.5 for substitution mechanics).

### 6.0 `<head>` Structure

The `<head>` section contains, in order:

**Meta tags:**

| Tag | Value | Purpose |
|---|---|---|
| `<meta charset="UTF-8">` | — | Character encoding |
| `<meta name="viewport">` | `width=device-width, initial-scale=1.0` | Responsive layout |
| `<meta name="color-scheme">` | `light dark` | Tells the browser to render native form controls (checkboxes, radio buttons, sliders, text inputs) in the appropriate theme. Without this, some browsers render light-mode controls even when `prefers-color-scheme: dark` matches. This is functional, not cosmetic. |
| `<meta name="description">` | `Compress PDFs to monochrome CCITT Group 4 format offline` | SEO / accessibility |
| `<meta name="apple-mobile-web-app-capable">` | `yes` | iOS PWA: allow fullscreen |
| `<meta name="apple-mobile-web-app-status-bar-style">` | `black` | iOS PWA: status bar color |
| `<meta name="apple-mobile-web-app-title">` | `PDF G4 Compressor` | iOS PWA: home screen name |

**Title:** `PDF Monochrome CCITT G4 Compressor`

**PWA manifest:** Inlined as a base64 data URL in `<link rel="manifest" href="data:application/json;base64,...">`. Contains app name, short name, description, `start_url: "./"`, `display: standalone`, colors, and an SVG icon as a data URL. The manifest source file `manifest.json` in the source tree is for reference only — the inlined version is the one used.

**Main `<style>` block:** ~1830 lines of CSS covering all UI components, dark mode, RTL, Mongolian vertical writing, intro animation, Flat Earth background, AI auto-setter, and responsive breakpoints. The `@font-face` declaration for Noto Sans Mongolian uses the `{{MONGOLIAN_FONT_BASE64}}` placeholder.

**Intro loading `<script>` (separate from `{{JAVASCRIPT}}`):** A small inline script block in `<head>` that runs before `<body>` loads:

```html
<script>
    document.documentElement.classList.add('intro-mode-loading');
</script>
```

This adds the `intro-mode-loading` class to `<html>` immediately, before any content renders. It must be in `<head>` (not in the `{{JAVASCRIPT}}` block at the end of `<body>`) because it needs to prevent the container from being visible during the initial paint.

**Intro loading `<style>` (separate from the main `<style>`):** Immediately after the script, a second small style block:

```html
<style>
    html.intro-mode-loading .container {
        opacity: 0 !important;
    }
</style>
```

This hides the main container while the intro animation plays. The `!important` is necessary because the main style block sets `opacity` transitions on `.container`. This second style block is separate from the main `<style>` because it is semantically distinct (temporary loading state, not permanent styling) and because the intro `<script>` sits between them.

### 6.0.1 `<body>` Top-Level Structure

The `<body>` contains these top-level children in order:

1. `<div class="fe-bg" id="feBg">` — Flat Earth background container (empty by default, populated dynamically by `feInit()` when a `-FE` locale is active).
2. `<a class="github-corner">` — GitHub corner link (top-right SVG, see section 41).
3. `<main class="container">` — The main application UI. This is a `<main>` element, not a `<div>`, which has semantic significance for screen readers (identifies the main content region). Contains all form controls, upload area, progress/result area, credits footer, modals, help/language buttons, and the debug preview section.
4. `{{JAVASCRIPT}}` — Replaced at build time with the assembled `<script>` block (section 3.1.1).

### 6.0.2 File Input

The file input is a hidden `<input type="file">` with:

```html
<input type="file" id="pdfFile" accept="application/pdf,application/zip,.pdf,.zip">
```

The `accept` attribute lists both MIME types (`application/pdf`, `application/zip`) and file extensions (`.pdf`, `.zip`). Both forms are needed because some browsers/platforms honor only MIME types and others only extensions. The input is visually hidden — the upload area `<div>` acts as its click target via a `<label>` wrapper.

### 6.0.3 Debug Preview Section

Near the bottom of `<main>`, before the credits footer, a hidden debug section:

```html
<div id="debugPreview" style="display:none; ...">
    <h3>Preview (for debugging)</h3>
    <div style="overflow: auto; max-height: 400px; ...">
        <canvas id="previewCanvas"></canvas>
    </div>
    <div id="previewInfo"></div>
</div>
```

This is not displayed to users (`display:none` inline style). It exists for development: when uncommented/enabled in the JS, it shows rendered page previews and metadata. The `previewCanvas` and `previewInfo` IDs are referenced in the DOM element assignment block of the `DOMContentLoaded` handler but not actively used in production.

### 6.1 Layout

- Single `.container` (`<main>` element) card centered on a gradient background (`#667eea` → `#764ba2`).
- Upload area with drag-and-drop support.
- Options panel with radio groups for: Conversion Mode (no-dither/dither/dither-selected), Page Size (A4/Letter/Legal in portrait/landscape), Output DPI (Standard 310 / Custom 72-1200).
- Compress button (`div[role="button"]` with keyboard support).
- Progress/result area.
- Credits footer with links to License, About, and Privacy modals.
- Language switch checkbox ("Use English") and Mongolian switch checkbox.
- Help button (bottom-left corner, replays intro animation).
- Language selector button (bottom-left, above help button).
- GitHub corner link (top-right, hidden in Android app until a modal is opened).

### 6.2 Modals

All four modals share the same structure: an outer `<div>` with `role="dialog"` and `aria-modal="true"`, containing a `.modal-content` div with a close button (`<button class="modal-close" aria-label="Close">&times;</button>`) as its first child. Modals are shown/hidden by adding/removing the `.show` class on the outer div. The `AndroidModalState.setModalOpen(true/false)` interface is called when modals are opened/closed (for Android back button handling, section 20.4).

#### 6.2.1 License Modal (`id="licenseModal"`)

- Close button: `id="closeLicense"`
- Title: `<h2 id="licenseModalTitle">License & Attributions</h2>` (referenced by `aria-labelledby`)
- Content: Multiple `.license-section` divs listing the project license (Apache 2.0) and all third-party components (PDF.js, pako, G4Enc, jbig2enc, Leptonica, LibTIFF, Noto Sans Mongolian) with copyright, license type, and URLs. Also includes a "Projects Studied (No Code Copied)" section for img2pdf. Ends with the full Apache 2.0 license text in a `<pre>` block.
- **Source tarball section** (`.source-section`):
  - Toggle link: `<a id="sourceToggle">▶ Get the source tarball in base64</a>` — clicking expands/collapses `#sourceContent`.
  - Content div: `id="sourceContent"` (hidden by default via `.source-content` CSS).
  - Readonly textarea: `id="sourceTextarea"` — populated by JavaScript with `SOURCE_TARBALL_BASE64` when the toggle is first opened.
  - Download link: `<a id="sourceDownload" download="pdf-g4-compressor-source-base64.txt">Download as .txt file</a>` — browser path creates a Blob URL; Android path wraps in a second base64 layer via `btoa()` so `AndroidFileHandler.saveFile()` decodes back to the original text.
  - Hint text: extraction command `base64 -d file.txt > source.tar.xz && tar -xJf source.tar.xz`.

#### 6.2.2 About Modal (`id="aboutModal"`)

- Close button: `id="closeAbout"`
- Title: `<h2 id="aboutModalTitle">About This Project</h2>` (referenced by `aria-labelledby`)
- Opening quote: _"We were so preoccupied with whether we could, we didn't stop to think if we should."_
- Content sections (each in a `.license-section` div):
  1. **"Why This Exists"** — Motivation for CCITT G4 and JBIG2 compression, and the self-contained tarball challenge.
  2. **"Architecture: A Study in Questionable Decisions"** — ASCII art showing the nested file structure (loader → compressed app → source tarball), described as "like a turducken, but for web apps."
  3. **"The 'AI' Button"** — Explains the ironic quotation marks and what the button actually does.
  4. **"Privacy Policy"** — Collapsible section:
     - Toggle link: `<a id="privacyToggle">▶ View Privacy Policy</a>`
     - Content: `id="privacyContent"` — contains the privacy icon SVG (see section 6.2.5) and the full privacy policy text with sections: Summary, Data Collection, Data Processing, Data Sharing, Third-Party Services, Open Source, Children's Privacy, Changes to This Policy, Contact, Your Rights.
  5. **"Disclaimer"** — "The absurdity is purely architectural." Includes "Generated with Claude on April 1, 2026" and "Source code may contain nuts (and tarballs)."
- **Self-download section** (`.source-section`):
  - Toggle link: `<a id="appDownloadToggle">▶ The ultimate inception: download this app itself</a>`
  - Content: `id="appDownloadContent"` — "It's like looking in a mirror that's also a photocopier."
  - Download link: `<a id="appDownloadBtn">Download this app as .html file</a>` — browser path creates a Blob from `window.PRISTINE_HTML`; Android path base64-encodes it via `btoa(unescape(encodeURIComponent(html)))` and calls `AndroidFileHandler.saveFile()` (section 46.13).

#### 6.2.3 Privacy Modal (`id="privacyModal"`)

- Close button: `id="closePrivacy"`
- Title: `<h2 id="privacyModalTitle">Privacy Policy</h2>` (referenced by `aria-labelledby`)
- Privacy icon: `<div class="privacy-icon-container" aria-hidden="true">` containing the privacy icon SVG (section 6.2.5). The `aria-hidden="true"` hides the decorative icon from screen readers.
- Content: The same full privacy policy text as in the About modal (duplicated in the template, not shared via JavaScript).

This is a standalone modal opened via the `#showPrivacy` link on the privacy notice line above the upload area. It is separate from the collapsible privacy section inside the About modal.

#### 6.2.4 Language Modal (`id="languageModal"`)

- Close button: `id="closeLanguageModal"`
- Uses `aria-label="Select Language"` directly on the outer div — unlike the other three modals which use `aria-labelledby` pointing to an `<h2>` title element. The Language modal has no visible `<h2>` title.
- Content: `<div class="language-list" id="languageList">` — populated dynamically by `populateLanguageList()` in the DOMContentLoaded handler. Renders a grid of buttons, one per language, showing the native language name from the `LANGUAGE_NAMES` constant (section 46.15). Joke locales (FE variants, 67) are conditionally shown based on the visibility rules in section 46.16.

#### 6.2.5 Privacy Icon SVG

The privacy icon appears in two places: the About modal's privacy section and the standalone Privacy modal. The markup is duplicated (not shared). Both are identical SVG elements with `class="privacy-cloud-icon"` and `viewBox="0 0 100 80"`:

- **Globe** (behind cloud): circle `cx=62 cy=40 r=20` (outline), vertical ellipse `rx=9 ry=20` (meridian), horizontal line y=40 (equator), vertical line x=62 (prime meridian). Stroke `#3498db` (blue), opacity 0.75.
- **Cloud** (partly covering globe): quadratic bezier path forming a cloud shape, filled `rgba(255,255,255,0.9)`, stroked `#667eea` (app purple).
- **Wireless signal**: solid dot at `cx=50 cy=54 r=2`, three concentric quarter-circle arcs (radii 8, 12, 16) above the dot. All in `#667eea`.
- **Red cross**: two diagonal lines from `(20,20)→(80,65)` and `(80,20)→(20,65)`, stroke `#e74c3c` (red), width 3, round caps.

The combined image conveys "no cloud/network connectivity" — a globe with wireless signal crossed out.

### 6.2.6 Credits Footer

Inside `<main class="container">`, after the debug preview section, the `.credits` div contains:

1. `<p data-i18n="credits">` — Third-party component names.
2. `<p><a id="showLicense" data-i18n="license">` — Opens License modal.
3. `<p><a id="showAbout" data-i18n="about">` — Opens About modal.
4. `<p id="appVersion">` — Shows `{app_version}` (replaced at build time).
5. `<div id="languageSwitch">` — "Use English" checkbox (shown via `.show` class when detected language ≠ English).
6. `<div id="mongolianSwitch">` — Traditional Mongolian checkbox (shown for Mongolia/mainland China regions).

The `#showPrivacy` link is NOT in the credits footer — it is on the privacy notice line (`<p class="subtitle">`) above the upload area. Clicking it opens the standalone Privacy modal.

### 6.2.7 GitHub Corner

An `<a class="github-corner">` element (top-right of the viewport) containing an inline SVG:

```html
<svg width="40" height="40" viewBox="0 0 250 250"
     style="fill:#667eea; color:#fff; position: absolute; top: 0; border: 0; right: 0;"
     aria-hidden="true">
```

The SVG contains three `<path>` elements:
- A triangular background wedge (`M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z`) filled with the `fill` color (#667eea, app purple).
- The octicon arm (`class="octo-arm"`): the waving tentacle, filled with `currentColor` (#fff). Has `transform-origin: 130px 106px` for the CSS wave animation.
- The octicon body (`class="octo-body"`): the main octocat silhouette, filled with `currentColor`.

Visibility is controlled via inline `style.display` by JavaScript (not a CSS class toggle). See section 41 for the complete visibility logic. The link opens in a new tab (`target="_blank" rel="noopener noreferrer"`).

### 6.2.8 Language Selector Button

A `<button class="language-selector-button" id="languageSelectorBtn" aria-label="Select Language">` positioned at the bottom-left of the viewport (above the help button). Contains an inline SVG with `viewBox="0 0 50 50"` showing overlapping script characters representing the app's multilingual support:

| Layer | Character | Script | Position | Size | Opacity |
|---|---|---|---|---|---|
| 1 (bottom) | A | Latin | x=4 y=29 | 40 | 0.9 |
| 2 | 文 | Chinese (Han) | x=22 y=27 | 36 | 0.95 |
| 3 | ع | Arabic (Ain) | x=6 y=47 | 32 | 0.85 |
| 4 | अ | Devanagari | x=30 y=47 | 32 | 1.0 |
| 5 (top) | ᠮ | Traditional Mongolian | x=42 y=31 | 28 | 0.9 |

The Mongolian character uses `font-family="'Noto Sans Mongolian', serif"` and is rotated 90° clockwise via `transform="rotate(90 42 31)"` (because Traditional Mongolian is a vertical script — rotating it fits the horizontal button layout). All characters use serif font, white fill with varying opacity, and are `aria-hidden="true"` (the button's `aria-label` provides the accessible name).

### 6.3 CSS Features

- Dark mode via `@media (prefers-color-scheme: dark)` with CSS custom properties.
- RTL support via `[dir="rtl"]` selectors.
- Traditional Mongolian vertical writing via `body.mongolian-script .container { writing-mode: vertical-lr; }`.
- Reduced motion support: `@media (prefers-reduced-motion: reduce)` disables animations.
- PWA manifest inlined as a base64 data URL in `<link rel="manifest">`.
- Noto Sans Mongolian loaded via `@font-face` with base64 data URL.

### 6.4 Important CSS Classes

#### 6.4.1 Body State Classes

These classes are added/removed on `<html>` or `<body>` by JavaScript to toggle major UI modes:

| Class | Element | Purpose | Set by |
|---|---|---|---|
| `.intro-mode-loading` | `<html>` | Hides `.container` (`opacity: 0 !important`) during intro animation. | `<head>` inline script (section 6.0), removed by intro.js `start()` and `step5_exitIntro()` |
| `.converting` | `<body>` | Hides help/language buttons during manual conversion. | Compress button handler, removed in `finally` block |
| `.ai-running` | `<body>` | Hides options, compress button, and progress area during AI auto-setter. | `runAutoSetter()`, removed on completion |
| `.flat-earth` | `<body>` | Activates Flat Earth background (shows `.fe-bg`). | DOMContentLoaded init for `-FE` locales |
| `.mongolian-script` | `<body>` | Activates `writing-mode: vertical-lr` on `.container`. | DOMContentLoaded init for `mn-Mong` locale |
| `.fe-intro-active` | `<body>` | During intro animation with Flat Earth mode: raises `.fe-bg` to `z-index: 99999` with `pointer-events: none`. | intro.js, removed in cleanup |

**Exact hiding rules for `body.ai-running` and `body.converting`:**

```css
body.ai-running .options,
body.ai-running #convertBtn,
body.ai-running #progress { display: none !important; }

body.ai-running .help-button,
body.ai-running .language-selector-button,
body.converting .help-button,
body.converting .language-selector-button { display: none !important; }
```

So `body.ai-running` hides 5 elements (options panel, compress button, progress area, help button, language selector button). `body.converting` hides only 2 elements (help button, language selector button) — the options and progress remain visible during manual conversion.

#### 6.4.2 Upload Area State Classes

| Class | Purpose |
|---|---|
| `.upload-area.dragover` | Visual feedback during drag-and-drop hover (border color/style change). |
| `.upload-area.file-error` | Red border and light red background on upload area when file validation fails (wrong type, unreadable). |

#### 6.4.3 DPI and Warning Classes

| Class | Purpose |
|---|---|
| `.dpi-dimensions` | Container for pixel dimension text below the DPI slider. Shows calculated page dimensions at the selected DPI. |
| `.dpi-warning.show` | Makes the warning div visible (default is hidden). |
| `.dpi-warning.low-quality` | Yellow warning for DPI below quality threshold (DPI < 200 no-dither or < 240 dither). |
| `.dpi-warning.high-filesize` | Orange warning for estimated RAM > 400 MB but within limit. |
| `.dpi-warning.high-compute` | Red warning for estimated RAM exceeding RAM_LIMIT — blocks the compress button. |

The three severity classes are mutually exclusive — `updateDPIWarning()` removes all three and adds the appropriate one.

#### 6.4.4 Progress and Button State Classes

| Class | Purpose |
|---|---|
| `#progress.cancelled` | Applied when conversion is cancelled or a file is re-selected while a result is showing. Changes background, text color, and text alignment. Contains the Advanced Tricks section in collapsed state. |
| `.action-btn.disabled` | Grayed-out styling for the compress button (which is a `div[role="button"]`, not an HTML `<button>`). Paired with `button:disabled` in a combined selector for consistent disabled styling across both real buttons and div-based buttons. |
| `.action-btn.saving` | Applied to the save button during save. Sets `pointer-events: none` and `opacity: 0.7`. The `::after` pseudo-element creates an inline spinning indicator: 16×16 px border circle with a white top edge, animated via `@keyframes spin` at 0.8s linear infinite. |

#### 6.4.5 Flat Earth CSS Rules

All Flat Earth classes are under `body.flat-earth .fe-bg { display: block; ... }` — without the body class, `.fe-bg` is `display: none`.

| Class / Keyframes | Purpose |
|---|---|
| `.fe-bg` | Fixed-position full-screen container behind the main content. Dark background with radial gradient (`#0d1137` → `#050520`). |
| `.fe-bg::before` | Starfield: a pseudo-element with multiple `radial-gradient` dots and a `fe-twinkle` opacity animation. |
| `@keyframes fe-twinkle` | Starfield twinkle: `opacity: 0.5` ↔ `1.0`, 6s ease-in-out infinite alternate. |
| `.fe-world-wrapper` | 340×500 px absolute-positioned container for one flat earth disc instance. |
| `.fe-world` | 340×340 px inner container with `perspective: 600px`. Holds the 3D-projected disc. |
| `.fe-slab` | Full-size element with `transform-style: preserve-3d; transform: rotateX(58deg)`. Creates the isometric disc tilt. |
| `.fe-top` | Circular face of the disc (`border-radius: 50%`, `translateZ(15px)`). Contains the SVG world map. |
| `.fe-side` | Side rings of the disc (repeated with different `translateZ` values for thickness). |
| `.fe-sun-orbit` | Container for the sun, with `animation: fe-sun-spin linear infinite` (duration set dynamically: 7–11s). |
| `.fe-sun` | 14×14 px radial-gradient circle (white center → yellow → orange → transparent) with glow box-shadow. Positioned at top of orbit, translated `Z(35px)` above the disc. |
| `@keyframes fe-sun-spin` | Rotates from `rotateZ(0deg)` to `rotateZ(-360deg)` at `translateZ(15px)`. |
| `.fe-water-back`, `.fe-water-front` | 340×500 px canvas layers for particle waterfall. Back layer at `z-index: 1` (behind disc), front at `z-index: 3` (in front). |

#### 6.4.6 AI Auto-Setter CSS Rules

The AI auto-setter button is dynamically created by `createAutoSetterButton()`. It is hidden by default (`display: none`) and shown via `.ai-autosetter.show`.

| Class | Purpose |
|---|---|
| `.ai-autosetter` | Main container. Gradient background, rounded corners, min-height, cursor pointer. Has hover scale and active press transforms (disabled when `.running`). |
| `.ai-autosetter.show` | `display: block` — makes the button visible. |
| `.ai-autosetter.running` | Disables hover/active animations (`cursor: default; animation: none`). |
| `.ai-progress-bar` | Inner progress bar with gradient fill and CSS `transform: scaleX()` animation. |
| `.ai-sparkles` | Container for particle sparkle effects (absolute-positioned). |
| `.ai-sparkle` | Individual sparkle: small element with radial gradient and `@keyframes` animation for floating and fading. |
| `.ai-star-shape` | Four-point star SVG shape used as a sparkle variant. |
| `.ai-content` | Inner content area of the button (padding, min-height, flex layout). |
| `.ai-label` | "AI" text label styling. |
| `.ai-row` | Horizontal layout row containing unicorns and text. Scales down on small screens (`transform: scale(0.85)` at narrow viewport). |
| `.ai-text-main` | Main descriptive text inside the button. |
| `.ai-unicorn-svg` | SVG unicorn sizing and positioning. |
| `.ai-unicorn-wrap` | Wrapper for unicorn + rainbow arc pair. |
| `.ai-status-text` | Status/ETA text shown during auto-setter execution. |
| `.ai-rainbow-lucky`, `.ai-rainbow-happy` | SVG rainbow arcs with `stroke-dashoffset` animation. Lucky rainbow plays every 0–5 min, happy rainbow every 0–1 min. |

#### 6.4.7 AI Refresh Box

| Class | Purpose |
|---|---|
| `.ai-refresh` | Container for the plain refresh icon button. `display: none` by default, shown via `.ai-refresh.show` as `display: flex`. Replaces the AI button when the user modifies form controls. |

#### 6.4.8 Fabulous Save Button and Win Banner

Created by `makeSaveFabulous()` after a successful AI auto-setter run:

| Class | Purpose |
|---|---|
| `.save-fabulous` | Wraps the save button with animated gradient background and sparkle effects. |
| `.save-fab-text` | Text styling inside the fabulous button. |
| `.save-fab-cloud` | Decorative cloud shape behind the button. |
| `.save-fab-stars` | Container for animated star decorations. |
| `.save-fab-sparkle` | Individual sparkle particles with keyframe animations. Disabled under `prefers-reduced-motion`. |
| `.save-fab-star` | Star shapes with rotation animation. Disabled under `prefers-reduced-motion`. |
| `.save-win-banner` | Banner displayed above the save button ("Best result found!"). |
| `.win-text` | Banner text styling. |
| `.win-sparkles` | Sparkle container within the banner. |

#### 6.4.9 Mongolian Vertical Writing Overrides

In vertical writing mode (`body.mongolian-script`), CSS `min-height` becomes the cross-axis dimension. Three elements need explicit `min-width` to prevent collapsing:

```css
body.mongolian-script .container .ai-autosetter { min-height: none; min-width: 130px; }
body.mongolian-script .container .ai-content { min-height: none; min-width: 130px; }
body.mongolian-script .container .ai-refresh { min-height: none; min-width: 130px; }
```

#### 6.4.10 Other Functional Classes

| Class | Purpose |
|---|---|
| `.input-hint-box` | Dismissible warning shown below the upload area when the file may not compress well (section 38). Visible via `.input-hint-box.show`. |
| `.show` | Generic visibility toggle used on multiple elements: `#languageSwitch.show`, `#mongolianSwitch.show`, `#dpiSliderContainer.show`, `#pageRangeContainer.show`, `.dpi-warning.show`, `.ai-autosetter.show`, `.ai-refresh.show`, `.input-hint-box.show`, and modal `.show` classes. |
| `.github-corner` | The GitHub octicon link (top-right). Visibility controlled via inline `style.display` by JavaScript (section 41), not via CSS class toggle. |

### 6.5 Internationalized Elements

The template contains 25 elements with `data-i18n` attributes. The `applyTranslations()` function (section 8.3) iterates these and sets either `textContent` or `placeholder` (for text inputs) from the `TRANSLATIONS[lang]` object.

| i18n Key | Element | Tag | Translation target |
|---|---|---|---|
| `title` | `<h1>` | h1 | `textContent` |
| `subtitle` | `<p class="subtitle">` | p | `textContent` |
| `privacyNotice` | `<span>` inside `#showPrivacy` link | span | `textContent` |
| `chooseFile` | `<label for="pdfFile">` (`#uploadAreaLabel`) | label | `textContent` |
| `conversionMode` | `<span>` (`#conversionModeLabel`) | span | `textContent` |
| `noDither` | `<label for="noDither">` | label | `textContent` |
| `dither` | `<label for="dither">` | label | `textContent` |
| `ditherSelected` | `<label for="ditherSelected">` | label | `textContent` |
| `pageRangePlaceholder` | `<input type="text" id="pageRange">` | input | **`placeholder`** (not textContent) |
| `pageRangeHint` | `<div id="pageRangeHint">` | div | `textContent` |
| `pageSize` | `<span>` (`#pageSizeLabel`) | span | `textContent` |
| `pageSizeA4Portrait` | `<label for="pageSizeA4Portrait">` | label | `textContent` |
| `pageSizeA4Landscape` | `<label for="pageSizeA4Landscape">` | label | `textContent` |
| `pageSizeLetterPortrait` | `<label for="pageSizeLetterPortrait">` | label | `textContent` |
| `pageSizeLetterLandscape` | `<label for="pageSizeLetterLandscape">` | label | `textContent` |
| `pageSizeLegalPortrait` | `<label for="pageSizeLegalPortrait">` | label | `textContent` |
| `outputDpi` | `<span>` (`#outputDpiLabel`) | span | `textContent` |
| `dpiStandard` | `<label for="dpiStandard">` | label | `textContent` |
| `dpiCustom` | `<label for="dpiCustom">` | label | `textContent` |
| `dpiHint` | `<div class="input-hint">` (no ID) | div | `textContent` |
| `compressButton` | `<div id="convertBtn">` | div | `textContent` |
| `processing` | `<span id="progressText">` | span | `textContent` |
| `credits` | `<p>` (no ID, in `.credits`) | p | `textContent` |
| `license` | `<a id="showLicense">` | a | `textContent` |
| `about` | `<a id="showAbout">` | a | `textContent` |

The `pageRangePlaceholder` key is the only one that sets `placeholder` instead of `textContent`. This is because it targets an `<input type="text">` — the `applyTranslations()` function detects `element.tagName === 'INPUT' && element.type === 'text'` and applies the translation to the placeholder attribute rather than the text content.

The `processing` element (`#progressText`) is recreated in the inline JS every time a conversion starts (`progressDiv.innerHTML = '<span class="spinner"></span><span id="progressText" data-i18n="processing">Processing...</span>'`), so it uses the English default initially and is re-translated if the language changes during conversion.

Additional i18n keys (such as `resultSaveButton`, `advancedTricks`, `useJBIG2Label`, `inputHint`, `ramWarningHigh`, etc.) are not in the static template — they are used in dynamically generated HTML created by `buildAdvancedTricksHTML()`, `showResultBox()`, `updateCompressButton()`, `updateInputHint()`, and other functions in the inline JS. These functions read `TRANSLATIONS[currentLang]` directly at call time rather than relying on the `data-i18n` attribute scan.

The `data-i18n-template` mechanism (section 8.3) is implemented in `applyTranslations()` but no elements in the current static template or dynamically generated HTML use it. It stores a template string on the element's `data-i18n-template-text` attribute for later `{placeholder}` substitution by JavaScript — the mechanism exists for potential future use.

---

## 7. JavaScript Modules

All code is assembled into a single `<script>` block by build.py (see section 3.1.1 for the complete assembly structure). Some items are read from external `.js` files; others are written inline in build.py's Python f-string. All execute in global scope.

### 7.1 Module Load Order

Items marked **[file]** are read from external `.js` files. Items marked **[inline]** exist only inside build.py's f-string.

1. Source tarball constant (`SOURCE_TARBALL_BASE64`) — **[inline]**, data from `create_source_tarball()`
2. pako (MIT, zlib compression) — **[file]** `libs/pako.min.js`
3. Merged i18n (translations + locale detection) — **[file]** `i18n.js` + `i18n-languages.js`, merged by build.py
4. PDF.js library — **[file]** `libs/pdf.legacy.min.js`
5. PDF.js worker (base64 → Blob URL) — **[inline]** IIFE (section 3.1.3), data from `libs/pdf.worker.legacy.min.js`
6. G4Enc (CCITT Group 4 encoder) — **[file]** `g4enc.js`
7. JBIG2 WASM binary (base64 → Uint8Array on `window._jbig2WasmBytes`) — **[inline]** IIFE, data from `wasm/jbig2.wasm`
8. JBIG2 loader source assignment (`window._jbig2LoaderSource`) — **[inline]**, JSON-escaped content of patched `wasm/jbig2.js`
9. JBIG2 initial Module object + first-time loader execution — **[inline]** + **[file]** `wasm/jbig2.js` (raw, in global scope)
10. `initJBIG2Module()` function for re-initialization — **[inline]**
11. JBIG2 Wrapper (JBIG2Encoder class) — **[file]** `jbig2-wrapper.js`
12. JBIG2 PDF generator — **[file]** `jbig2pdf.js`
13. Image processing pipeline — **[file]** `imageprocessing.js`
14. PDF generation (CCITT G4) — **[file]** `pdfgen.js`
15. PDF stream compressor — **[file]** `pdfcompress.js`
16. ZIP utilities — **[file]** `ziputil.js`
17. Intro animation — **[file]** `intro.js`
18. Flat Earth background — **[file]** `flatearth.js` (with `FLATEARTH_PATHS_PLACEHOLDER` replaced by build.py)
19. Pristine HTML fallback (section 3.1.4) — **[inline]**
20. State machine comment block (documentation only) — **[inline]**, ~77 lines
21. Global variables + `defaultResultSettings()` + DOM ref declarations — **[inline]**
22. `pageshow` event listener (bfcache restore) — **[inline]**
23. `resetAppState()` function — **[inline]**, ~150 lines
24. `DOMContentLoaded` handler (main application logic) — **[inline]**, ~3,370 lines (see section 3.1.1 for internal structure)

---

## 8. Internationalization

### 8.1 Supported Languages

83 languages total, including:

**Standard languages:** af, am, ar, as, az, be, bg, bn, bo, bs, ca, cs, da, de, el, en, es, et, eu, fa, fi, fr, gl, gu, he, hi, hr, hu, hy, id, is, it, ja, jv, ka, kk, km, kn, ko, ky, lo, lt, lv, mk, ml, mn, mn-Mong, mr, ms, my, nb, ne, nl, nn, or, pa, pl, pt, ro, ru, si, sk, sl, sq, sr-Cyrl, sr-Latn, sv, sw, ta, te, tg, th, tk, tl, tr, tt, uk, ur, uz, vi, yi, zh-Hans, zh-Hant, zu

**Joke locales:** en-FE (English Flat Earth), cs-FE (Czech Flat Earth), sk-FE (Slovak Flat Earth), 67 (Internet slang/Gen-Z)

**RTL languages:** ar, he, ur, yi — detected and applied via `document.body.setAttribute('dir', 'rtl')`.

**Vertical script:** mn-Mong (Traditional Mongolian script, Unicode U+1800–U+18AF) — uses `writing-mode: vertical-lr` on the container. Note: `mn` is modern Cyrillic Mongolian (for Mongolia); `mn-Mong` is the traditional vertical script (for Inner Mongolia, China). Both are separate translations.

### 8.2 Locale Detection

The `detectLanguage()` function in i18n.js (full algorithm in section 46.1):
1. Reads `navigator.languages` (array of preferred locales) or falls back to `navigator.language`.
2. Normalizes each locale to BCP 47 casing via `normalizeBCP47()` (section 46.1).
3. For each locale, tries: exact TRANSLATIONS match → LOCALE_FALLBACK lookup (section 46.2) → base language match.
4. Falls back to `en`.

### 8.3 Translation Application

`applyTranslations(langCode)` (full algorithm in section 46.3):
- Sets `document.documentElement.lang` for screen readers.
- Sets body `dir="rtl"` for RTL languages `{ar, he, ur, yi}`, `dir="ltr"` otherwise.
- Iterates all elements with `data-i18n` attributes: for `<input type="text">` sets `placeholder`, for all others sets `textContent`.
- Iterates all elements with `data-i18n-template` attributes: stores the translated template string in a `data-i18n-template-text` attribute for later JS substitution of `{placeholders}`.

### 8.4 Language Switching

Three mechanisms:
1. "Use English" checkbox — toggles between detected language and English.
2. "ᠮᠣᠩᠭᠣᠯ ᠬᠡᠷᠡᠭᠯᠡᠬᠦ" checkbox — toggles Traditional Mongolian.
3. Language selector modal — grid of all languages, clicking one switches immediately.

The Mongolian checkbox is only shown to users in Mongolia or mainland China (Inner Mongolia). It is NOT shown to users in Taiwan, Hong Kong, Macau, or Singapore. The exact relevant regions checked: `mn`, `mn-MN`, `mn-Mong`, `mn-Mong-MN`, `mn-Mong-CN`, `zh-CN`, `zh-Hans`, `zh-Hans-CN`.

On every language change (via any of the three mechanisms), the app: applies translations, updates DPI warning text, re-renders the result/cancelled box if one is visible (`showResultBox()` or `showCancelledBox()`), re-renders the AI button label, updates the input hint box, and calls `saveAppState()`.

### 8.5 April 1st Easter Egg

On April 1st, the locale is automatically switched to a Flat Earth variant if the user's base language is en, cs, or sk. The mapping is: en → en-FE, cs → cs-FE, sk → sk-FE.

### 8.6 i18n File Structure

`i18n.js` contains: the `RTL_LANGUAGES` set, the `LOCALE_FALLBACK` table, the `TRANSLATIONS` object with 6 core languages inline (en, de, es, pt, cs, sk), locale detection and translation functions. It ends with the marker `// Continue in next file due to length...`. `i18n-languages.js` contains `const ADDITIONAL_TRANSLATIONS = {...}` with all remaining languages. During build, the content of `ADDITIONAL_TRANSLATIONS` is spliced into the `TRANSLATIONS` object by replacing the marker comment (see also section 46.4).

Each translation is an object with 47 required keys plus optional keys for additional messages.

### 8.7 Required Translation Keys

The i18n-validate.js validator checks for these 47 required fields: title, subtitle, privacyNotice, chooseFile, conversionMode, noDither, dither, ditherSelected, pageRangePlaceholder, pageRangeHint, pageSize, pageSizeA4Portrait, pageSizeA4Landscape, pageSizeLetterPortrait, pageSizeLetterLandscape, pageSizeLegalPortrait, outputDpi, dpiStandard, dpiCustom, dpiHint, compressButton, processing, credits, license, about, lowQualityWarning, resultSaveButton, resultRecommendIgnore, resultDidntCompressWell, resultBecameBigger, resultAppPurpose, resultDitheringNote, resultDitheringAdvice, advancedTricks, useJBIG2Label, jbig2Warning, preserveRotationLabel, metadataSection, includeTimestampLabel, ramWarningHigh, ramWarningCritical, jbig2DisabledMpix, jbig2DisabledPages, ramOverrideAcceptRisk, fileInfoPageCount, fileInfoFileSize, inputHint.

---

## 9. Image Processing Pipeline

File: `imageprocessing.js` (225 lines)

The pipeline replicates the behavior of the GraphicsMagick command sequence used in the CLI tools (see section 31.1). All functions are pure — they allocate new output arrays and do not mutate their inputs. Every function returns `{data: Uint8Array|Float32Array, width: number, height: number}`.

### 9.1 Common Data Formats

**Intermediate format** (between pipeline steps 1–3): `{data: Uint8Array, width, height}` where `data` is one byte per pixel, 0 (black) to 255 (white), row-major, no padding.

**Final bilevel format** (output of step 4): `{data: Uint8Array, width, height}` where `data` is packed bilevel — 1 bit per pixel, MSB first within each byte, rows padded to byte boundaries (`bytesPerRow = Math.ceil(width / 8)`). Bit value 1 = black pixel, 0 = white pixel. This is the opposite polarity from the G4 encoder's convention (section 10.2).

### 9.2 Step 1: Grayscale Conversion

```
rgbaToGrayscale(imageData) → {data: Uint8Array, width, height}
```

**Input**: A canvas `ImageData` object (has `.data` as `Uint8ClampedArray` of RGBA quads, `.width`, `.height`).

**Algorithm**: Iterates the RGBA array in steps of 4. For each pixel, computes luminance using Rec. 601 luma weights:

```
grayscale[j] = Math.round(0.299 * R + 0.587 * G + 0.114 * B)
```

The alpha channel is ignored — all pixels are treated as fully opaque.

### 9.3 Step 2: Histogram Normalization

```
normalize(image) → {data: Uint8Array, width, height}
```

**Input**: An intermediate image `{data: Uint8Array, width, height}`.

**Algorithm**: Finds the global minimum and maximum pixel values across the entire image, then linearly stretches the histogram so that `min` maps to 0 and `max` maps to 255:

```
normalized[i] = Math.round(((data[i] - min) * 255) / (max - min))
```

**Edge-case guard**: If `max === min` (uniform image — all pixels have the same value), the function copies the input data unchanged and returns. This prevents division by zero.

### 9.4 Step 3: Level Adjustment

```
applyLevels(image, blackPercent = 10, whitePercent = 90) → {data: Uint8Array, width, height}
```

**Input**: An intermediate image. `blackPercent` and `whitePercent` are configurable — the defaults (10, 90) match the GraphicsMagick `-level 10%,90%` command.

**Algorithm**: Computes black and white point thresholds as fractions of 255:

```
blackPoint = (blackPercent / 100) * 255   // default: 25.5
whitePoint = (whitePercent / 100) * 255   // default: 229.5
```

For each pixel:
- `value <= blackPoint` → 0 (black)
- `value >= whitePoint` → 255 (white)
- Between: linear interpolation `Math.round(((value - blackPoint) * 255) / (whitePoint - blackPoint))`

**Edge-case guard**: If `whitePoint - blackPoint === 0` (degenerate range), the function copies the input data unchanged and returns.

### 9.5 Step 4: Bilevel Conversion

Two functions, selected by the `dither` option:

#### 9.5.1 Without Dithering

```
toBilevelNoDither(image, threshold = 128) → {data: Uint8Array, width, height}
```

Simple thresholding: `value < threshold` → black (bit = 1), `value >= threshold` → white (bit = 0). Output is packed MSB-first into bytes, rows padded to byte boundaries. The output `Uint8Array` is zero-initialized, so white pixels (bit 0) require no action; only black pixels are explicitly set.

#### 9.5.2 With Floyd-Steinberg Dithering

```
toBilevelDithered(image, threshold = 128) → {data: Uint8Array, width, height}
```

Creates a `Float32Array` copy of the input data (to accumulate fractional error values without clamping). For each pixel in raster order:

1. Read the current (error-adjusted) value from the working array.
2. Quantize: if `value < threshold` → new pixel is 0 (black, bit = 1), else → 255 (white, bit = 0).
3. Compute error: `error = oldPixel - newPixel` (can be negative or positive).
4. Distribute error to unprocessed neighbors using the standard Floyd-Steinberg kernel:

```
        X    7/16
  3/16  5/16  1/16
```

Specifically:
- Right neighbor `(x+1, y)`: `+= error * 7/16`
- Below-left `(x-1, y+1)`: `+= error * 3/16`
- Below `(x, y+1)`: `+= error * 5/16`
- Below-right `(x+1, y+1)`: `+= error * 1/16`

Each distribution is guarded by a boundary check (no wrap-around at edges).

### 9.6 Pipeline Entry Point

```
processImage(imageData, options = {}) → {data: Uint8Array, width, height}
```

**Input**: A canvas `ImageData` object and an options object.

**Options object fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `dither` | boolean | `false` | If true, use Floyd-Steinberg dithering; if false, use simple thresholding |
| `threshold` | number | `128` | Bilevel quantization threshold (0–255) |
| `blackLevel` | number | `10` | Black point percentage for level adjustment (passed to `applyLevels` as `blackPercent`) |
| `whiteLevel` | number | `90` | White point percentage for level adjustment (passed to `applyLevels` as `whitePercent`) |

The function chains the four steps in order:

1. `rgbaToGrayscale(imageData)`
2. `normalize(result)`
3. `applyLevels(result, blackLevel, whiteLevel)`
4. `toBilevelDithered(result, threshold)` or `toBilevelNoDither(result, threshold)`

Each step allocates a new output array; the previous step's data becomes eligible for GC.

Note: although `threshold`, `blackLevel`, and `whiteLevel` are configurable in the function signature, the application always calls `processImage()` with default options (only `dither` is set explicitly). The configurability exists for testing and potential future use.

### 9.7 Module Export

```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        rgbaToGrayscale, normalize, applyLevels,
        toBilevelNoDither, toBilevelDithered, processImage
    };
}
```

All six functions are exported individually for Node.js testing. In the browser build, `module` is undefined and the guard is a no-op — all functions are available as globals. This same export pattern is used in 6 of 7 JS module files (g4enc.js, imageprocessing.js, pdfgen.js, jbig2pdf.js, jbig2-wrapper.js, pdfcompress.js). The exception is ziputil.js, which declares functions in global scope with no export guard.

---

## 10. CCITT Group 4 Encoder

File: `g4enc.js` (608 lines)

Ported from C to JavaScript from [G4ENC by Larry Bank](https://github.com/bitbank2/G4ENC) (Apache 2.0).

### 10.1 API

```javascript
const encoder = new G4Encoder();
encoder.init(width, height, G4ENC_MSB_FIRST);
for (let y = 0; y < height; y++) {
    const result = encoder.addLine(rowData);
    if (result === G4ENC_IMAGE_COMPLETE) break;
}
const compressedData = encoder.getData();
```

### 10.2 Polarity Convention

The G4 encoder expects bit=1 for WHITE pixels. The bilevel output from `processImage()` uses bit=1 for BLACK. Therefore, the application inverts the bilevel data in-place before feeding it to the encoder:
```javascript
for (let i = 0; i < processed.data.length; i++) {
    processed.data[i] = ~processed.data[i] & 0xFF;
}
```

### 10.3 Buffer Sizing

`OUTPUT_BUF_SIZE = 131072` (128 KB). Worst case at 1200 DPI on A4 (9924 pixels wide): ~4962 runs/line × 19 bits/run ≈ 11.8 KB/line. 128 KB provides a 10× safety margin.

`G4ENC_MAX_WIDTH = 16384`. Supports up to ~1400 DPI on A4.

### 10.4 Constants and Lookup Tables

**Constants:**

| Constant | Value | Notes |
|---|---|---|
| `G4ENC_MSB_FIRST` | 1 | Bit fill order: MSB first (default, used by this application) |
| `G4ENC_LSB_FIRST` | 2 | Bit fill order: LSB first (supported via `ucMirror` reversal table) |
| `OUTPUT_BUF_SIZE` | 131072 | 128 KB output buffer |
| `G4ENC_MAX_WIDTH` | 16384 | Maximum supported image width in pixels |
| `REGISTER_WIDTH` | 32 | Bit accumulator width |
| `G4ENC_SUCCESS` | 0 | Return: line encoded successfully |
| `G4ENC_NOT_INITIALIZED` | 1 | Return: encoder not initialized |
| `G4ENC_INVALID_PARAMETER` | 2 | Return: bad parameter |
| `G4ENC_DATA_OVERFLOW` | 3 | Return: defined but currently unused |
| `G4ENC_IMAGE_COMPLETE` | 4 | Return: last line encoded, data ready |

**Lookup tables:**

- `bitcount` (Uint8Array, 256 entries): Maps a byte value to the number of consecutive 1-bits from the MSB. Examples: `bitcount[0x00]=0`, `bitcount[0x80]=1`, `bitcount[0xC0]=2`, `bitcount[0xFF]=8`. Used in `encodeLine()` to scan for run boundaries within bytes.

- `vtable` (Uint8Array, 14 entries): Vertical mode code/length pairs indexed by `(dx + 3) * 2` where dx = b1 − a1 (range −3 to +3). Example: V(0) = `{1, 1}` (single `1` bit), V(−1) = `{3, 3}` (`011`), V(+1) = `{2, 3}` (`010`).

- `huff_white` (Uint16Array, 128 entries): White terminating Huffman codes for runs 0–63. Stored as code/length pairs: `huff_white[run*2]` = code, `huff_white[run*2+1]` = bit length.

- `huff_wmuc` (Uint16Array, 80 entries): White make-up Huffman codes for runs 64–2496 (in multiples of 64). Index = `run / 64`. Entry 0 is unused (run-length 0 is invalid for make-up).

- `huff_black` (Uint16Array, 128 entries): Black terminating codes for runs 0–63.

- `huff_bmuc` (Uint16Array, 80 entries): Black make-up codes for runs 64–2496.

- `ucMirror` (Uint8Array, 256 entries): Full bit-reversal table. `ucMirror[0x01]=0x80`, `ucMirror[0x80]=0x01`, etc. Applied to every output byte when `fillOrder === G4ENC_LSB_FIRST`. Not used when encoding MSB-first (the default).

### 10.5 Constructor and Internal State

```javascript
class G4Encoder {
    constructor() {
        this.width = 0;          // Image width in pixels
        this.height = 0;         // Image height in pixels
        this.y = 0;              // Current line number (0-indexed)
        this.fillOrder = G4ENC_MSB_FIRST;
        this.dataSize = 0;       // Total compressed output bytes so far
        this.error = G4ENC_SUCCESS;

        this.bb = {              // Bit buffer (32-bit register)
            buf: new Uint8Array(OUTPUT_BUF_SIZE),  // Current output buffer
            bufPos: 0,           // Write position in buf
            bits: 0,             // 32-bit accumulator (codes shifted in from MSB)
            bitOff: 0            // Number of valid bits in accumulator (0-31)
        };

        this.output = [];        // Array of Uint8Array chunks (flushed buffers)

        this.curFlips = new Int16Array(G4ENC_MAX_WIDTH);  // Current line run-ends
        this.refFlips = new Int16Array(G4ENC_MAX_WIDTH);  // Reference line run-ends
    }
}
```

The `output` array collects completed buffer chunks. Each time the buffer fills, `flushBuffer()` slices the used portion, pushes it to `output`, increments `dataSize`, and allocates a fresh buffer. `getData()` concatenates all chunks into a single `Uint8Array`.

### 10.6 Methods

**`init(width, height, bitDirection = G4ENC_MSB_FIRST)`** — Validates parameters, sets dimensions and fill order, initializes both `curFlips` and `refFlips` to all-`width` (representing an all-white imaginary reference line before line 0), resets the bit buffer. Returns `G4ENC_SUCCESS` or `G4ENC_INVALID_PARAMETER`.

**`addLine(pixels)`** — Main encoding entry point. Called once per scan line. Does the following:
1. Checks the high-water mark: if `bb.bufPos >= iHighWater` (where `iHighWater = OUTPUT_BUF_SIZE - 4096`, i.e., 124 KB), calls `flushBuffer()`. This flush happens BETWEEN lines, never mid-line. The original C code used a threshold of `OUTPUT_BUF_SIZE - 8`; the JS port increased the margin for safety.
2. Calls `encodeLine(pixels)` to convert the raw pixel data into run-end format in `curFlips`.
3. Runs the G4 encoding loop over `curFlips` vs `refFlips` (see section 10.8).
4. On the last line (`y === height - 1`): emits two EOL codes (`insertCode(1, 12)` twice), calls `flushBits()`, pushes the final buffer to `output`.
5. Swaps `curFlips` and `refFlips` (the current line becomes the reference for the next line).
6. Increments `y`. Returns `G4ENC_IMAGE_COMPLETE` on the last line, `G4ENC_SUCCESS` otherwise.

**`getData()`** — Concatenates all chunks in `this.output` into a single `Uint8Array` of size `this.dataSize`. Called once after encoding is complete.

**`getOutSize()`** — Returns `this.dataSize`.

### 10.7 Bit Buffer and Buffer Management

The encoder accumulates compressed bits in a 32-bit register (`bb.bits`) with a position counter (`bb.bitOff`). When the register would overflow (more than 32 bits), the top 4 bytes are written to the buffer in big-endian order and the remaining bits stay in the register.

**`insertCode(code, len)`** — Shifts `code` into the 32-bit register at position `bb.bitOff`. If `bb.bitOff + len > 32`: writes 4 bytes to `bb.buf`, shifts the overflow bits into a fresh register. If the buffer is within 4 bytes of capacity, calls `flushBuffer()` first (this is a safety check that should not trigger in practice due to the between-lines high-water flush).

**`flushBits()`** — Writes all remaining bits in the register to the buffer, including the final partial byte (zero-padded). Resets `bb.bits` and `bb.bitOff` to 0. Called only once, after the two EOL codes on the last line.

**`flushCompleteBytes()`** — Writes only complete bytes (groups of 8 bits) from the register to the buffer. Partial bits (fewer than 8) remain in the register with `bb.bits` and `bb.bitOff` preserved. Called by `flushBuffer()` before slicing the buffer to output, ensuring no partial-byte data is lost during the buffer swap.

**`flushBuffer()`** — The multi-chunk output mechanism:
1. Calls `flushCompleteBytes()` to drain complete bytes from the register to the buffer.
2. If `fillOrder === G4ENC_LSB_FIRST`, applies `reverseBits()` to the buffer.
3. Slices `bb.buf[0..bufPos]` and pushes the slice to `this.output`.
4. Adds `bufPos` to `this.dataSize`.
5. Allocates a fresh `Uint8Array(OUTPUT_BUF_SIZE)` for the next chunk.
6. Resets `bb.bufPos` to 0. **Does NOT reset `bb.bits` or `bb.bitOff`** — partial bits carry over to the new buffer.

**`reverseBits(data, len)`** — Applies the `ucMirror` lookup table to each byte. Only used when `fillOrder === G4ENC_LSB_FIRST`.

### 10.8 G4 Encoding Loop

The encoding loop in `addLine()` implements the three ITU T.6 modes. It walks the current line (`curFlips`) against the reference line (`refFlips`) using run-end positions:

- **a0**: Current position on the coding line (starts at 0)
- **a0_c**: Color at a0 (0 = white, 1 = black)
- **a1**: `curFlips[iCur]` — next color change on the current line at or after a0
- **b1**: `refFlips[iRef]` — next color change on the reference line of opposite color to a0_c
- **b2**: `refFlips[iRef + 1]` — the color change after b1 on the reference line

Mode selection per iteration:

1. **Pass mode** (b2 < a1): The reference line has a pair of color changes before the current line's next change. Emit pass code `0001` (code=1, len=4). Advance a0 to b2, advance iRef by 2.

2. **Vertical mode** (|b1 − a1| ≤ 3): The current line's color change is within 3 pixels of the reference line's. Emit the vertical code from `vtable[(dx+3)*2]` where dx = b1 − a1. Advance a0 to a1, toggle a0_c, advance iCur and iRef. After advancing, scan iRef forward to find the next reference color change after the new a0.

3. **Horizontal mode** (|b1 − a1| > 3): Emit horizontal code `001` (code=1, len=3), then two run-length codes. If a0_c is white: emit white run (a1 − a0) then black run (a1' − a1). If a0_c is black: emit black run then white run. Advance a0 past both runs, advance iCur by 2, scan iRef forward.

The loop terminates when a0 reaches `xsize` (image width).

### 10.9 Run-End Encoding (`encodeLine`)

`encodeLine(pixels)` converts a row of packed bilevel pixel bytes into run-end format in `curFlips`. The algorithm scans bytes using the `bitcount` table to count consecutive 1-bits (white pixels, since the data has been inverted before reaching the encoder) and complemented bytes for 0-bits (black pixels).

The key boundary handling: for widths not divisible by 8, the final byte contains padding bits. The `xborder` variable tracks remaining valid pixels and clamps run lengths when `xborder < 0` (padding reached). After the scanning loop, the final position is clamped: `if (x > xsize) x = xsize`.

The run-end array is terminated with 4 copies of `xsize` as a sentinel (ensures the G4 encoding loop's lookahead reads `xsize` for any out-of-bounds access).

### 10.10 Run-Length Huffman Encoding

**`addWhite(len)` / `addBlack(len)`** — Encode a run of pixels as Huffman codes:

1. While `len >= 64`:
   - If `len >= 2560`: emit the special escape code `{0x1f, 12}` and subtract 2560. This handles runs beyond the make-up table range by emitting the escape repeatedly.
   - Otherwise: compute make-up index `len >>> 6` (integer division by 64), emit `huff_wmuc[index*2]` / `huff_bmuc[index*2]` with corresponding length. Reduce `len` to `len & 63` (remainder).
2. Emit the terminating code `huff_white[len*2]` / `huff_black[len*2]` for the remaining 0–63 pixels. A terminating code is always emitted, even when `len` is 0 after make-up codes.

### 10.11 Diagnostic Logging

On the first scan line (`y === 0`), `addLine()` emits detailed diagnostic output to `console.log`:
- Image width and bytes per row
- First 20 bytes of the pixel data (hex, after polarity inversion)
- First 64 decoded pixels as a `W`/`B` character string
- Run count and first 10 entries of `curFlips` and `refFlips`
- Bit buffer state (`bufPos`, `bits`, `bitOff`)
- A warning if run count exceeds 1000 (suspiciously high, may indicate incorrect input)
- For the first 5 iterations of the G4 encoding loop: `a0`, `a0_c`, `a1`, `b2`, chosen mode, and emitted codes

This logging is always active (not gated by a debug flag) and appears in the browser console during every first-page compression.

### 10.12 Module Export

The file ends with:
```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { G4Encoder, G4ENC_MSB_FIRST, G4ENC_LSB_FIRST };
}
```

This allows the encoder to be used in Node.js environments for testing. In the browser build, `module` is undefined and the guard is a no-op — `G4Encoder` and the constants are available as globals.

---

## 11. JBIG2 Compression System

### 11.1 WASM Module

Files: `wasm/jbig2.wasm`, `wasm/jbig2.js`

The WASM module is compiled from [jbig2enc](https://github.com/agl/jbig2enc) (Apache 2.0) with [Leptonica](https://github.com/DanBloomberg/leptonica) (BSD 2-Clause) using Emscripten.

A patch (`jbig2enc-emscripten.patch`) replaces POSIX `open()/write()/close()` with `fopen()/fwrite()/fclose()` to enable Emscripten's MEMFS virtual filesystem.

Pinned versions: Leptonica v1.84.1, jbig2enc at commit 4cadbfe.

Build command: `./build-jbig2-wasm.sh` (requires Emscripten SDK).

### 11.2 WASM Initialization

On page load:
1. The WASM binary is base64-decoded to `window._jbig2WasmBytes`.
2. The patched Emscripten loader source is stored as `window._jbig2LoaderSource`.
3. `window.Module` is created with `wasmBinary`, `noInitialRun: true`, and callbacks.
4. The Emscripten loader runs in global scope (first-time init via `var` hoisting).
5. `window.JBIG2Ready` is set to `true` when `onRuntimeInitialized` fires.

Re-initialization (for fresh heap between conversions):
```javascript
function initJBIG2Module() {
    window.JBIG2Ready = false;
    window.Module = { wasmBinary: window._jbig2WasmBytes, ... };
    (new Function(window._jbig2LoaderSource))();
}
```

The `new Function()` approach is required because the Emscripten loader uses `var Module = ...` which hoists in `new Function()` scope but would conflict in global scope on re-evaluation.

### 11.3 JBIG2Encoder Wrapper

File: `jbig2-wrapper.js` (231 lines)

Class: `JBIG2Encoder` — high-level JavaScript API over the jbig2enc WASM module. Manages the MEMFS working directory, PBM file creation, argument construction, and output file collection.

#### 11.3.1 Constructor and State

```javascript
constructor() {
    this.module = null;        // Reference to window.Module (set by init())
    this.initialized = false;
    this.workDir = '/jbig2_work';
    this.pageCount = 0;        // Number of pages added via addPage()
}
```

#### 11.3.2 `init()`

```
async init() → void
```

Waits for the WASM module's Emscripten filesystem to become available. Returns a Promise that resolves when ready or rejects after timeout.

**Polling mechanism**: Checks every 10 ms (via `setTimeout(checkReady, 10)`) up to 1000 times (10 seconds total). Each check tests for three specific `FS` methods:
- `window.Module.FS.mkdir` — needed by `prepareEncoding()`
- `window.Module.FS.writeFile` — needed by `addPage()`
- `window.Module.FS.readFile` — needed by `encode()` to read output files

All three must be `typeof ... === 'function'` for initialization to succeed. If `window.Module` is undefined at call time, throws immediately (not via the polling path).

On success, sets `this.module = window.Module` and `this.initialized = true`. On timeout (1000 checks), rejects with `'JBIG2 initialization timeout'`.

If already initialized (`this.initialized === true`), returns immediately.

#### 11.3.3 `prepareEncoding()`

```
prepareEncoding() → void
```

Creates a clean `/jbig2_work/` directory in the WASM MEMFS and resets `this.pageCount` to 0. Must be called before `addPage()`.

**Defensive double-cleanup pattern**: Handles leftover state from previous runs that may not have completed (e.g., `encode()` was never called because the user cancelled conversion). The cleanup sequence is:

1. Try: `cleanupDirectory('/jbig2_work/')` then `FS.rmdir('/jbig2_work/')` — removes all contents and the directory.
2. Try: `FS.mkdir('/jbig2_work/')` — create fresh directory.
3. If `mkdir` fails (directory still exists due to a race or unremovable entry): repeat cleanup + rmdir, then `mkdir` again (no try/catch — this time a failure propagates).

All intermediate errors are silently caught. This ensures a clean workspace regardless of what state the MEMFS was left in.

#### 11.3.4 `addPage(width, height, bilevelData)`

```
addPage(width, height, bilevelData) → void
```

Writes a PBM file for one page into the WASM MEMFS. The caller can free `bilevelData` immediately after this returns — the data is now in the WASM filesystem, not in JS heap.

**PBM filename**: `page-${String(this.pageCount).padStart(4, '0')}.pbm` — zero-padded to 4 digits. Example: `page-0000.pbm`, `page-0001.pbm`, ..., `page-0119.pbm`.

**PBM creation** (`createPBM(width, height, data)` private method): Builds a Netpbm P4 (binary PBM) file by concatenating a text header and the raw bilevel data:

```
P4\n
{width} {height}\n
<raw bilevel bytes>
```

The header is encoded via `TextEncoder` (UTF-8, safe because the header is ASCII). The resulting `Uint8Array` is written to MEMFS via `FS.writeFile()`.

Increments `this.pageCount` after each page.

#### 11.3.5 `encode(options)`

```
async encode(options = {}) → {sym: Uint8Array|null, pages: Uint8Array[]}
```

Runs the jbig2enc encoder on all pages accumulated via `addPage()`. Throws if not initialized or if no pages were added.

**Options:**

| Field | Type | Default | Description |
|---|---|---|---|
| `lossy` | boolean | `true` | Enable lossy compression (symbol matching) |
| `threshold` | number | `0.97` | Symbol matching threshold (0.85, 0.92, or 0.97) |
| `symbolCoding` | boolean | `true` | Enable symbol dictionary (shared across pages) |
| `progressCallback` | function\|null | `null` | `(current, total, statusText)` progress reporter |

**Argument construction** — builds the `args` array for `Module.callMain()` in this exact order:

1. `-s` — if `symbolCoding` is true (enables symbol dictionary mode)
2. `-t {threshold}` — if `lossy` is true (two elements: `'-t'`, `String(threshold)`)
3. `-p` — always (output PDF-compatible JBIG2 segments)
4. `-b {workDir}/output` — always (two elements: `'-b'`, `'/jbig2_work/output'` — sets output file prefix)
5. Page filenames — one per page: `'/jbig2_work/page-0000.pbm'`, `'/jbig2_work/page-0001.pbm'`, etc.

Example for 3 pages with lossy, symbol coding, threshold 0.97:
```
['-s', '-t', '0.97', '-p', '-b', '/jbig2_work/output',
 '/jbig2_work/page-0000.pbm', '/jbig2_work/page-0001.pbm', '/jbig2_work/page-0002.pbm']
```

**Execution**: Calls `this.module.callMain(args)`. Checks the return value — if non-zero, throws `'JBIG2 encoding failed with exit code {N}'`.

**Output file collection**:

1. If `symbolCoding` is true: reads the global symbol dictionary from `/jbig2_work/output.sym` using `FS.analyzePath(path).exists` to check existence first. Stores as `result.sym` (`Uint8Array`).
2. For each page (0 to `pageCount-1`): reads `/jbig2_work/output.${String(i).padStart(4, '0')}` (e.g., `output.0000`, `output.0001`, ...). Throws if any expected page file is missing. Stores as `result.pages[]`.

**Cleanup** — in a `finally` block (runs even if encoding throws):

1. `cleanupDirectory('/jbig2_work/')` — recursively deletes all files and subdirectories.
2. `FS.rmdir('/jbig2_work/')` — removes the empty directory (silently catches errors).
3. Resets `this.pageCount = 0`.

The `finally` block ensures MEMFS is cleaned up regardless of success, failure, or cancellation. This is important because WASM linear memory cannot shrink — leftover files would persist until `initJBIG2Module()` destroys and recreates the entire WASM instance.

**Progress callback**: Called three times — at start `(0, total, 'Encoding with JBIG2')`, after encoding completes `(total, total, 'Reading output files')`, and after output collection `(total, total, 'Complete')`. No per-page progress is available during encoding because jbig2enc processes all pages in a single `callMain()` invocation.

**Console logging**: Logs page count before encoding, symbol dictionary size after encoding, and final summary (`sym=NB, M pages (NB total)`).

#### 11.3.6 `cleanupDirectory(dirPath)` (private)

Recursively removes all files and subdirectories under `dirPath` in the WASM MEMFS. Uses `FS.readdir()` to list entries (skipping `.` and `..`), `FS.stat()` + `FS.isDir()` to distinguish files from directories, `FS.unlink()` for files, and recursive `cleanupDirectory()` + `FS.rmdir()` for subdirectories. All errors are silently caught — partial cleanup is tolerated because `prepareEncoding()` will retry.

Guards against `this.module` or `this.module.FS` being null (returns immediately if either is missing), which can happen if cleanup is called after the WASM module has been destroyed by `initJBIG2Module()`.

#### 11.3.7 Module Export

```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = JBIG2Encoder;
}
```

Exports the class itself (not wrapped in an object, unlike pdfgen.js which exports `{ createPDF }`). In the browser build, `JBIG2Encoder` is available as a global.

### 11.4 JBIG2 Encoding Flow

1. `prepareEncoding()` creates clean workspace.
2. For each page: `renderPDFPages` renders to bilevel, then calls `encoder.addPage()` which writes a PBM file to MEMFS. The bilevel data in JS is immediately freed (`processed.data = null`).
3. `encoder.encode()` runs jbig2enc via `Module.callMain()` with flags `-s -t <threshold> -p -b /jbig2_work/output` followed by all page filenames (see section 11.3.5 for exact argument order):
   - `-s` enables symbol coding (symbol dictionary shared across pages).
   - `-t` sets the matching threshold.
   - `-p` outputs PDF-compatible segments.
   - `-b` sets the output file prefix.
4. Output files: `output.sym` (global symbol dictionary) and `output.0000` through `output.NNNN` (per-page segments). Cleanup and output collection happen in the `finally` block of `encode()` (section 11.3.5).

### 11.5 JBIG2 Patent Considerations

This implementation uses only non-patented features of JBIG2: basic encoding, symbol dictionary, and lossy compression with threshold. Performance optimizations covered by patents are excluded. The threshold values (0.85/0.92/0.97) provide good compression without patented techniques.

### 11.6 JBIG2 vs CCITT G4 Comparison

| Aspect | CCITT G4 | JBIG2 |
|---|---|---|
| Compression type | Lossless | Lossy (symbol matching) |
| Typical size | 10-80 KB/page | 5-50 KB/page (30-50% smaller) |
| Encoding speed | Fast (~1-2 ms/page) | Slower (symbol dictionary creation) |
| PDF version required | 1.0+ | 1.4+ |
| Reader compatibility | Universal | Modern readers (post-2010) |
| Character confusion risk | None | Possible at lower thresholds |
| Best for | All documents | Text-heavy, multi-page documents |
| Avoid for | — | Documents requiring character-level fidelity |

### 11.7 JBIG2 Feasibility Limits

- Maximum total megapixels: 475 Mpix (Leptonica 5M symbol limit).
- Maximum pages per PDF: 120 (hard cap).
- If exceeded, the JBIG2 checkbox is disabled and grayed out with an explanation message.

### 11.8 JBIG2 PDF Generation

File: `jbig2pdf.js`

One exported function: `createJBIG2PDF` (PDF/A-1B generator). The `md5` helper is module-private.

#### 11.8.1 `createJBIG2PDF({ globalData, pages, metadataOptions })`

```
createJBIG2PDF({
    globalData: Uint8Array|null,   // Global symbol dictionary (output.sym)
    pages: Array<{                 // Per-page segment data (output.NNNN)
        width: number,
        height: number,
        data: Uint8Array,
        pageWidthPt?: number,      // defaults to 595 (A4)
        pageHeightPt?: number,     // defaults to 842 (A4)
        rotate?: number            // optional /Rotate value
    }>,
    metadataOptions?: {
        includeProducer?: boolean,  // default true
        includeTimestamp?: boolean  // default true
    }
}) → Uint8Array
```

Creates a PDF/A-1B file. The structure is nearly identical to `createPDF` in pdfgen.js (section 12.1) with two key differences: the filter is `/JBIG2Decode` instead of `/CCITTFaxDecode`, and a global symbol dictionary object may be present.

**Object layout:**

```
  1              Global dictionary stream (only if globalData is non-null)
  2..N*3+1       Per-page objects (image, content, page) × N pages
  N*3+1+G        Pages object            (G = 1 if globalData, 0 otherwise)
  N*3+2+G        XMP Metadata stream
  N*3+3+G        OutputIntent
  N*3+4+G        Catalog
```

The `pagesObjNum` is pre-calculated as `1 + (globalData ? 1 : 0) + pages.length * 3`. When `globalData` is present, it occupies object 1, shifting all subsequent objects by 1 compared to pdfgen.js.

**Global symbol dictionary**: If `globalData` is non-null, a stream object is created with just `/Length` and no filter — the raw symbol dictionary bytes. Its object number (`globalObjNum`) is referenced by every page's image XObject.

**Per-page image XObject**: Same CalGray colorspace and structure as pdfgen.js (section 12.1.2), but with:
```
/Filter /JBIG2Decode
/DecodeParms << /JBIG2Globals {globalObjNum} 0 R >>
```

If no global dictionary is present, `/DecodeParms << >>` is used (empty dictionary).

**Content stream length**: Uses `contentStream.length` (JavaScript string length) for the `/Length` value. Since the content stream is pure ASCII, string length equals byte length. (In pdfgen.js, the content stream is first encoded to bytes and byte length is used — the result is identical for ASCII content, but the approach differs.)

**Page sizing, centering, rotation, metadata, OutputIntent, Catalog**: Identical to pdfgen.js (sections 12.2–12.4, 12.1.3). Constants `A4_WIDTH_PT=595` and `A4_HEIGHT_PT=842` are redefined locally (duplicating pdfgen.js values — each module is self-contained).

#### 11.8.2 File ID Generation (`md5` function)

The file ID is generated differently from pdfgen.js:

**Input**: `"${timestamp}${pages.length}"` — e.g., `"2026-05-06T12:34:56+00:005"` (the XMP timestamp concatenated with the page count, no separator).

**Hash function** (named `md5` but NOT MD5): Uses the same algorithm as `simpleHash` in pdfgen.js (section 12.5) — the Java `String.hashCode()` algorithm (`hash * 31 + char`, truncated to 32 bits). The name `md5` is misleading and historical.

**Output formatting** differs from pdfgen.js: The 8-character hex hash is repeated 4 times and truncated to 32 characters:

```javascript
let hex = Math.abs(hash).toString(16).padStart(8, '0');
return (hex + hex + hex + hex).substring(0, 32);
```

This produces a 32-character string with a repeating pattern (e.g., `"A1B2C3D4A1B2C3D4A1B2C3D4A1B2C3D4"`). In contrast, pdfgen.js zero-pads a shorter hash to 32 characters, producing leading zeros.

Both approaches produce valid PDF file IDs. The difference is cosmetic.

#### 11.8.3 Module Export

```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createJBIG2PDF };
}
```

`createJBIG2PDF` is the sole export. The `md5` helper is module-private.

---

## 12. PDF Generation

### 12.1 CCITT G4 PDF (pdfgen.js)

File: `pdfgen.js` (247 lines)

Creates PDF/A-1B from CCITT Group 4 compressed page data. The single entry point is `createPDF(pages, metadataOptions)`.

**`pages`** — Array of page objects, each with:
- `width`, `height` — Image dimensions in pixels.
- `data` — `Uint8Array` of CCITT G4 compressed stream (from `G4Encoder.getData()`).
- `pageWidthPt`, `pageHeightPt` (optional) — Target page size in points. Defaults to `A4_WIDTH_PT=595`, `A4_HEIGHT_PT=842` if not provided. The application sets these per-page based on the user's page size selection (section 12.2).
- `rotate` (optional) — PDF rotation value (e.g., 270). If present, a `/Rotate` entry is added to the page object.

**`metadataOptions`** — Object with optional fields `includeProducer` (boolean, default `true`) and `includeTimestamp` (boolean, default `true`). See section 12.4.

**Returns**: `Uint8Array` containing the complete PDF file.

### 12.1.1 PDF File Structure

The file begins with a PDF 1.4 header followed by a binary marker:

```
%PDF-1.4\n
<0x25 0xE2 0xE3 0xCF 0xD3 0x0A>
```

The binary marker (a `%` followed by four bytes with values > 127) signals to transport layers that the file contains binary data. This is required for PDF/A compliance.

Objects are numbered sequentially starting at 1. Each page produces 3 objects (image XObject, content stream, page object), followed by global objects:

```
Object layout:
  1..N*3     Per-page objects (image, content, page) × N pages
  N*3+1      Pages object (parent of all page objects)
  N*3+2      XMP Metadata stream
  N*3+3      OutputIntent
  N*3+4      Catalog (root object)
```

The `pagesObjNum` (Pages object number) is pre-calculated as `1 + pages.length * 3` before any objects are written. This allows page objects to reference their parent before the Pages object itself is emitted.

### 12.1.2 Per-Page Objects

For each page, three objects are created in order:

**1. Image XObject:**
```
<< /Type /XObject /Subtype /Image
   /Width W /Height H
   /ColorSpace [/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]
   /BitsPerComponent 1
   /Filter /CCITTFaxDecode
   /DecodeParms << /K -1 /BlackIs1 false /Columns W /Rows H >>
   /Decode [0 1]
   /Length L >>
stream
<raw CCITT G4 data>
endstream
```

The CalGray colorspace with D65 white point `[0.9505 1.0000 1.0890]` is required for PDF/A-1B (DeviceGray is not allowed). `/K -1` specifies Group 4 encoding. `/BlackIs1 false` means bit=1 is white in the CCITT stream (matching the G4 encoder's convention after polarity inversion, section 10.2). `/Decode [0 1]` maps decoded values 0→0.0 (black) and 1→1.0 (white).

**2. Content Stream:**
```
<< /Length L >>
stream
q
{scaledWidth} 0 0 {scaledHeight} {xOffset} {yOffset} cm
/Im{i} Do
Q
endstream
```

The content stream places the image on the page using a CTM (Current Transformation Matrix). The `q`/`Q` pair saves/restores graphics state. The `cm` operator sets a matrix that scales and positions the image. `/Im{i} Do` paints image resource `Im0`, `Im1`, etc. All numeric values use `.toFixed(4)` precision (4 decimal places).

**3. Page Object:**
```
<< /Type /Page /Parent {pagesObjNum} 0 R
   /MediaBox [0 0 {pageWidthPt} {pageHeightPt}]
   [/Rotate {rotate}]
   /Resources << /XObject << /Im{i} {imgObjNum} 0 R >> >>
   /Contents {contentObjNum} 0 R >>
```

The `/Rotate` entry is only present when `page.rotate` is set (see section 12.3).

### 12.1.3 Global Objects

After all per-page objects:

**Pages Object:** `<< /Type /Pages /Kids [{page1} 0 R {page2} 0 R ...] /Count N >>`

**XMP Metadata Stream** (see section 12.4): Carries `/Type /Metadata /Subtype /XML`. The stream content is NOT compressed — XMP Metadata must remain uncompressed for PDF/A-1B compliance (the FlateDecode compressor in section 13 skips these objects).

**OutputIntent:** `<< /Type /OutputIntent /S /GTS_PDFA1 /OutputConditionIdentifier (Gray Gamma 2.2) /Info (Grayscale with Gamma 2.2) >>` — Required for PDF/A-1B.

**Catalog:** `<< /Type /Catalog /Pages {pagesObjNum} 0 R /Metadata {metadataObjNum} 0 R /OutputIntents [{outputIntentObjNum} 0 R] /MarkInfo << /Marked true >> /ViewerPreferences << /DisplayDocTitle true >> >>` — `/MarkInfo` and `/ViewerPreferences` are required for PDF/A-1B.

### 12.1.4 Cross-Reference Table and Trailer

After all objects, the xref table is written with byte offsets for each object (tracked by `offsets[]` during object emission). Object 0 is the conventional free-list head (`0000000000 65535 f`).

The trailer contains `/Size` (object count + 1), `/Root` (Catalog reference), and `/ID` (see section 12.5).

### 12.1.5 Assembly Strategy

The function accumulates output as an array of `Uint8Array` and string chunks (`parts[]`). A running `currentOffset` tracks the byte position (needed for xref offsets). Strings are converted to bytes via `TextEncoder`. After all content is written, a single `Uint8Array` of size `currentOffset` is allocated and all chunks are copied into it. This single-pass approach avoids building the entire PDF as a string and minimizes peak memory usage.

### 12.2 Page Sizing and Centering

The rendered image is scaled to fit the target page dimensions while maintaining aspect ratio. The scale factor is:

```javascript
const scale = imgAspect > pageAspect
    ? pageWidthPt / page.width    // image is wider than page → fit to width
    : pageHeightPt / page.height; // image is taller than page → fit to height
```

Centering offsets: `xOffset = (pageWidthPt - scaledWidth) / 2`, `yOffset = (pageHeightPt - scaledHeight) / 2`.

Page sizes supported (in inches → points at 72 DPI):
- A4 Portrait: 595 × 842 pt (8.27 × 11.69 in)
- A4 Landscape: 842 × 595 pt
- Letter Portrait: 612 × 792 pt (8.5 × 11 in)
- Letter Landscape: 792 × 612 pt
- US Legal Portrait: 612 × 1008 pt (8.5 × 14 in)

### 12.3 Page Rotation

When "Try to preserve page rotation" is enabled, for each page:
1. Get the viewport at scale 1.0 without and with 90° additional rotation.
2. Compare the scale factors: which rotation fills the target page better.
3. If 90° rotation improves coverage, render with the rotated viewport and add `/Rotate 270` to the PDF page object.

The `/Rotate 270` (not 90) compensates for the fact that the image was rendered in the rotated orientation.

### 12.4 Metadata Options

Two checkboxes in Advanced Tricks:
- **Include Producer**: Sets `pdf:Producer` and `xmp:CreatorTool` to "PDF Monochrome G4 Compressor". When unchecked, these fields are empty strings (not omitted — empty `<pdf:Producer></pdf:Producer>`).
- **Include Timestamps**: Sets `xmp:CreateDate`, `xmp:ModifyDate`, `xmp:MetadataDate` to current time. When unchecked, uses epoch (1970-01-01T00:00:00+00:00).

**Timestamp formatting**: JavaScript's `new Date().toISOString()` produces `2026-05-06T12:34:56.789Z`. The regex `.replace(/\.\d{3}Z$/, '+00:00')` strips the milliseconds and replaces the `Z` suffix with the explicit `+00:00` UTC offset required by XMP.

The XMP metadata stream follows the standard `<?xpacket?>` / `<x:xmpmeta>` / `<rdf:RDF>` structure with four `rdf:Description` blocks:
1. `dc:format` = `application/pdf`
2. `pdfaid:part` = `1`, `pdfaid:conformance` = `B` (PDF/A-1B declaration)
3. `xmp:CreateDate`, `xmp:ModifyDate`, `xmp:MetadataDate`, `xmp:CreatorTool`
4. `pdf:Producer`

### 12.5 File ID

**`generateFileId(pageCount)`** — Creates a 32-character uppercase hex string for the PDF `/ID` array.

Input string: `"${Date.now()}-${pageCount}-${Math.random()}"` (e.g., `"1714999200000-5-0.123456789"`).

This is passed through `simpleHash(str)`:

```javascript
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;  // hash * 31 + char
        hash = hash & hash;                   // truncate to 32-bit integer
    }
    return Math.abs(hash).toString(16);
}
```

This is equivalent to Java's `String.hashCode()` algorithm (multiply by 31, accumulate). The `hash & hash` idiom forces JavaScript to treat the value as a 32-bit integer (equivalent to `hash | 0` but preserving the sign for the `Math.abs` call).

The hex result (typically 1–8 characters) is then zero-padded and truncated:

```javascript
hash.padStart(32, '0').substring(0, 32).toUpperCase()
```

For short hashes, this produces a string with leading zeros (e.g., `"000000000000000000000000A1B2C3D4"`). Both entries in the PDF `/ID` array are identical (both are the same hash) since this is a newly-created file.

### 12.6 Module Export

```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createPDF };
}
```

Only `createPDF` is exported. The helper functions `generateFileId` and `simpleHash` are module-private but accessible as globals in the browser build.

---

## 13. PDF Stream Compressor

File: `pdfcompress.js` (345 lines)

Applies FlateDecode (zlib level 9 via pako) compression to every stream in the PDF, cascading on top of existing filters.

### 13.1 Entry Point

```
async compressPDF(pdfData, pako, progressCallback) → Uint8Array
```

**Parameters:**
- `pdfData` — `Uint8Array` of the input PDF (output from `createPDF` or `createJBIG2PDF`).
- `pako` — Reference to the pako library object.
- `progressCallback(current, total)` — Optional. Called with stream index and total object count.

**Returns:** `Uint8Array` of the compressed PDF.

The function is `async` to allow `setTimeout(0)` yields between objects, keeping the UI thread responsive during compression of large PDFs.

### 13.2 Binary-Safe Text Handling

All string decode/encode operations use `latin1` (ISO-8859-1) encoding:

```javascript
const decoder = new TextDecoder('latin1');
const encoder = new TextEncoder();  // always UTF-8, but used only for ASCII content
```

This is critical: PDF files contain binary stream data mixed with ASCII dictionary syntax. Using `latin1` ensures that every byte value (0x00–0xFF) round-trips through decode→string-manipulation→encode without corruption. UTF-8 decoding would mangle bytes ≥0x80. The `TextEncoder` (always UTF-8) is safe because it is only used to encode ASCII strings (object headers, xref entries, trailer text) — never binary data.

### 13.3 Algorithm

**Step 1 — Header detection:**

Scan the first `Math.min(100, pdfData.length)` bytes for a `\n` (0x0A) at position > 10. The first such newline marks the end of the `%PDF-1.x` header line plus the binary marker line. Everything before this position is preserved verbatim as the PDF header. The 100-byte scan limit is a safety bound — valid PDF headers are always well within this range.

**Step 2 — Locate xref:**

Find the byte pattern `xref\n` using `findPattern()`. Everything between the header end and the xref position contains the PDF objects.

**Step 3 — Parse objects:**

`findObjects()` decodes the object region as a `latin1` string and scans with the regex `/(\d+) 0 obj\s*/g`. For each match, it locates the corresponding `endobj` marker and extracts the object body (everything between `N 0 obj\n` and `endobj`) as a `Uint8Array` slice. Returns an array of `{num, start, end, data}`.

**Step 4 — Process each object:**

For each object, attempt to parse it as a stream object via `parseStreamObject()`. If it has no stream, keep the object data unchanged (counted as `skipped`). If it has a stream:

1. Parse the dictionary via `parseDict()` to extract `/Type`, `/Subtype`, `/Filter`, `/Length`.
2. **XMP Metadata skip**: If `type === 'Metadata'` or `subtype === 'XML'`, keep unchanged (`skipped`). XMP Metadata must remain uncompressed for PDF/A-1B compliance.
3. Compress the stream data: `pako.deflate(streamData, { level: 9 })`.
4. Build a new dictionary via `updateDictWithCompression()` with the compressed length and filter cascading.
5. Reassemble the object: `[newDict, '\nstream\n', compressedData, '\nendstream']`.
6. Track statistics: `compressed` (new FlateDecode added) or `cascaded` (FlateDecode added on top of existing filter).

**Step 5 — Rebuild PDF:**

Reassemble the complete PDF using a collect-and-concat strategy (avoids O(n²) incremental concatenation):

1. Start with the original header.
2. For each processed object: emit `{i+1} 0 obj\n`, the object body, `\nendobj\n`. Record the byte offset of each object for the xref table. Objects are renumbered sequentially starting at 1.
3. Write the xref table with the new offsets: object 0 is the free-list head (`0000000000 65535 f`), remaining objects use `{offset padded to 10 digits} 00000 n`.
4. Copy the trailer dictionary verbatim from the original PDF (the bytes between `trailer\n` and `startxref` in the input). This preserves the original `/Size`, `/Root`, and `/ID` entries.
5. Write `startxref\n{xrefOffset}\n%%EOF\n`.
6. Allocate a single `Uint8Array` of the total size and copy all parts into it.

**Step 6 — Log statistics:**

Prints to console: `"Compressed N streams, cascaded N, skipped N"` and `"Original: N bytes, Compressed: N bytes"`.

### 13.4 Helper Functions

**`findObjects(pdfData)`** — Decodes `pdfData` (Uint8Array, header-to-xref region) as `latin1`, scans with regex `/(\d+) 0 obj\s*/g`, finds matching `endobj` via `indexOf`. Returns `[{num, start, end, data: Uint8Array}]`.

**`parseStreamObject(objData)`** — Decodes `objData` as `latin1`. Finds stream boundaries using regex `/stream\s*\n/` for the start and `/\s*endstream/` for the end. Returns `{dictData: Uint8Array, streamData: Uint8Array}` or `{streamData: null}` if no stream is present. The dict data is everything before `stream`, the stream data is between `stream\n` and `endstream`.

**`parseDict(dictData)`** — Decodes `dictData` as `latin1` and extracts four fields via regex:

| Field | Regex | Captures |
|---|---|---|
| `length` | `/\/Length\s+(\d+)/` | Integer value |
| `filter` | `/\/Filter\s+(\/\w+\|\[[^\]]+\])/` | Single filter name or filter array string |
| `type` | `/\/Type\s+\/(\w+)/` | Type name without leading `/` |
| `subtype` | `/\/Subtype\s+\/(\w+)/` | Subtype name without leading `/` |

Returns `{length, filter, type, subtype, raw: Uint8Array}`.

**`updateDictWithCompression(dictData, newLength, cascadeFilter, existingFilter)`** — Decodes dictionary as `latin1`, then applies three regex replacements:

1. **Update length**: `/\/Length\s+\d+/` → `/Length {newLength}`.

2. **Add or cascade filter** (when `cascadeFilter` is truthy):
   - If `existingFilter` is non-null (existing single filter like `/CCITTFaxDecode`):
     - Replace `/\/Filter\s+\/\w+/` → `/Filter [ /FlateDecode {existing} ]`.
     - If `/DecodeParms` is present (matched by `/\/DecodeParms\s+(<<[^>]+>>)/`): replace with `/DecodeParms [ null {existingDecodeParms} ]`. The `null` entry corresponds to FlateDecode (which needs no decode parameters).
   - If `existingFilter` is null (no existing filter):
     - Replace `/(\/Length)/` → `/Filter /FlateDecode $1` (inserts FlateDecode before `/Length`).

3. Encodes the modified string back to bytes via `TextEncoder`.

**`findPattern(data, pattern)`** — Byte-level linear search. Scans `data` (Uint8Array) for the first occurrence of `pattern` (Uint8Array). Returns the byte offset or -1. Uses labeled `continue outer` for the inner loop mismatch.

**`concatArrays(arrays)`** — Concatenates an array of `Uint8Array`s into a single `Uint8Array`. Pre-calculates total length, allocates once, copies with `.set()`.

### 13.5 Cascading

The cascading approach means FlateDecode wraps around the existing compression. A PDF reader decompresses FlateDecode first, then applies the inner filter (CCITTFaxDecode or JBIG2Decode). This provides additional size reduction on top of the domain-specific compression.

### 13.6 Progress Callback Throttling

The progress callback is not called on every object. Instead, it is throttled to fire at most every 80 ms:

```javascript
const now = Date.now();
if (now - lastYield >= 80) {
    progressCallback(objIdx + 1, objects.length);
    await new Promise(r => setTimeout(r, 0));
    lastYield = Date.now();
}
```

The `setTimeout(0)` yield returns control to the browser event loop, allowing UI updates (progress text rendering) between compression bursts. The `lastYield` timestamp is updated AFTER the yield (not before), so the next 80 ms window starts from when work resumes.

### 13.7 Known Limitations

- **Single-filter cascading only**: The filter replacement regex `/\/Filter\s+\/\w+/` matches only a single filter name (e.g., `/Filter /CCITTFaxDecode`). If the input PDF already has a filter array (e.g., `/Filter [/FlateDecode /CCITTFaxDecode]`), the regex will not match and cascading will fail silently — the stream will be compressed but the filter entry will not be updated correctly. This is not a problem in practice because this compressor only processes PDFs generated by pdfgen.js or jbig2pdf.js, which always use single filters.

- **Shallow DecodeParms matching**: The `/DecodeParms` regex `/<<[^>]+>>/` cannot handle nested dictionaries (a `<<` inside the outer `<<...>>`). This is acceptable because the DecodeParms dictionaries generated by pdfgen.js and jbig2pdf.js are always flat (no nesting).

- **Trailer copied verbatim**: The trailer dictionary from the original PDF is copied as raw bytes. This means the `/Size` entry in the trailer may not match the new object count if objects were added or removed. In practice, `compressPDF` preserves the exact same number of objects (it never adds or removes objects, only replaces their content), so the `/Size` value remains correct.

### 13.8 Module Export

```javascript
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { compressPDF };
}
```

Only `compressPDF` is exported. The helper functions (`findObjects`, `parseStreamObject`, `parseDict`, `updateDictWithCompression`, `findPattern`, `concatArrays`) are module-private but accessible as globals in the browser build.

---

## 14. ZIP Processing

File: `ziputil.js` (215 lines)

### 14.1 CRC32

The file includes a self-contained CRC32 implementation used for ZIP entry checksums.

**Lookup table** (`CRC32_TABLE`): A `Uint32Array(256)` computed at load time in an IIFE. For each byte value 0–255, the table stores the CRC remainder after 8 iterations of the IEEE polynomial `0xEDB88320` (bit-reflected representation of the standard CRC-32 polynomial).

**`crc32(data)`**: Computes the CRC-32 checksum of a `Uint8Array`. Initializes with `0xFFFFFFFF`, XORs each byte against the low 8 bits of the accumulator to index the table, shifts right by 8, XORs with the table entry. Final result is inverted and zero-filled right-shifted (`>>> 0`) to ensure an unsigned 32-bit value.

### 14.2 ZIP Reader (`parseZip`)

```
parseZip(arrayBuffer) → [{path: string, data: Uint8Array}]
```

Parses a ZIP file from an `ArrayBuffer`. Uses both `Uint8Array` (for byte access) and `DataView` (for multi-byte little-endian field reads) over the same buffer.

**Step 1 — Find End of Central Directory (EOCD):**

Scans backwards from the end of the file looking for the EOCD signature `0x06054B50`. The search starts at `bytes.length - 22` (minimum EOCD size) and works toward offset 0. Throws `'Not a valid ZIP file'` if not found.

**Step 2 — Read EOCD fields:**

| EOCD offset | Size | Field | Usage |
|---|---|---|---|
| +10 | 2 bytes | Total CD entries | Loop count for step 3 |
| +16 | 4 bytes | CD offset | Start position of the central directory |

**Step 3 — Parse central directory entries:**

For each entry (signature `0x02014B50`):

| CD offset | Size | Field |
|---|---|---|
| +10 | 2 bytes | Compression method (0=stored, 8=deflated) |
| +20 | 4 bytes | Compressed size |
| +24 | 4 bytes | Uncompressed size |
| +28 | 2 bytes | Filename length |
| +30 | 2 bytes | Extra field length |
| +32 | 2 bytes | Comment length |
| +42 | 4 bytes | Local file header offset |
| +46 | N bytes | Filename (decoded as UTF-8 via `TextDecoder`) |

Directories (paths ending with `/`) are skipped.

The central directory entry points to a local file header. The local header must be read to compute the actual data offset because its extra field length may differ from the central directory's:

```
dataOffset = localHeaderOffset + 30 + localNameLen + localExtraLen
```

Where `localNameLen` is at local header offset +26 and `localExtraLen` is at +28.

**Step 4 — Extract data:**

- **Method 0 (stored)**: The data is copied via `.slice()` — NOT `.subarray()`. This creates an independent copy, decoupling it from the parent `ArrayBuffer` so the original ZIP data can be garbage-collected when nulled. This is critical for tier 1/2 memory management (section 34.17).
- **Method 8 (deflated)**: Decompressed via `pako.inflateRaw(compressedData)`.
- **Other methods**: Throws `'Unsupported compression method'`.

Advances the central directory offset by `46 + nameLen + extraLen + commentLen` to reach the next entry.

### 14.3 ZIP Writer (`createZip`)

```
createZip(entries) → Uint8Array
```

Creates a ZIP file from an array of `{path: string, data: Uint8Array}` entries.

**Per-entry processing:**

1. Encode the filename as UTF-8 via `TextEncoder`.
2. Compute CRC-32 of the uncompressed data.
3. Compress with `pako.deflateRaw(data)` (default compression level — NOT level 9; contrast with `pdfcompress.js` which uses level 9).
4. If compressed size ≥ uncompressed size: fall back to stored (method 0), using the original uncompressed data.

**Local file header** (30 + filename length bytes):

| Offset | Size | Value | Notes |
|---|---|---|---|
| 0 | 4 | `0x04034B50` | Local file header signature |
| 4 | 2 | 20 | Version needed to extract (2.0) |
| 6 | 2 | 0 | General purpose bit flags |
| 8 | 2 | 0 or 8 | Compression method |
| 10 | 2 | 0 | Last mod file time (**zeroed**) |
| 12 | 2 | 0 | Last mod file date (**zeroed**) |
| 14 | 4 | CRC-32 | CRC of uncompressed data |
| 18 | 4 | compressed size | |
| 22 | 4 | uncompressed size | |
| 26 | 2 | filename length | |
| 28 | 2 | 0 | Extra field length |
| 30 | N | filename bytes | |

**Central directory header** (46 + filename length bytes):

| Offset | Size | Value | Notes |
|---|---|---|---|
| 0 | 4 | `0x02014B50` | Central directory signature |
| 4 | 2 | 20 | Version made by (2.0) |
| 6 | 2 | 20 | Version needed (2.0) |
| 8 | 2 | 0 | Flags |
| 10 | 2 | 0 or 8 | Compression method |
| 12 | 2 | 0 | Last mod time (**zeroed**) |
| 14 | 2 | 0 | Last mod date (**zeroed**) |
| 16 | 4 | CRC-32 | |
| 20 | 4 | compressed size | |
| 24 | 4 | uncompressed size | |
| 28 | 2 | filename length | |
| 30 | 2 | 0 | Extra field length |
| 32 | 2 | 0 | File comment length |
| 34 | 2 | 0 | Disk number start |
| 36 | 2 | 0 | Internal file attributes |
| 38 | 4 | 0 | External file attributes |
| 42 | 4 | local header offset | |
| 46 | N | filename bytes | |

All timestamp, attribute, and disk-number fields are zeroed. The created ZIP carries no modification times.

**End of Central Directory** (22 bytes):

| Offset | Size | Value |
|---|---|---|
| 0 | 4 | `0x06054B50` |
| 4 | 2 | 0 (disk number) |
| 6 | 2 | 0 (disk with CD) |
| 8 | 2 | entry count (this disk) |
| 10 | 2 | entry count (total) |
| 12 | 4 | central directory size |
| 16 | 4 | central directory offset |
| 20 | 2 | 0 (comment length) |

**Assembly**: Allocates a single `Uint8Array` of exact total size (`cdOffset + cdSize + 22`). Copies local headers interleaved with data blobs, then central directory headers, then EOCD.

### 14.4 ZIP Mode

When a user selects a `.zip` file (detected by magic bytes `PK\x03\x04`):
- The "Dither only selected pages" option is disabled (no sense with multiple files).
- Each PDF in the ZIP is processed independently.
- The result is a new ZIP containing the compressed PDFs.
- Result filename: `original_ccittG4.zip` or `original_jbig2.zip`.

Result filename for single PDFs: `input.pdf` → `input_ccittG4.pdf` (G4 mode) or `input_jbig2.pdf` (JBIG2 mode). The `.pdf` extension is replaced via `file.name.replace('.pdf', '_ccittG4.pdf')`.

### 14.5 Known Limitations

- **No ZIP64 support**: The implementation uses 16-bit entry counts and 32-bit sizes/offsets throughout. Archives with more than 65,535 entries or individual files larger than ~4 GB cannot be handled. This is acceptable because the application processes scanned PDFs, which are well within these limits.

- **Only methods 0 and 8**: Stored and deflated are the only supported compression methods. Other methods (e.g., bzip2, LZMA) will throw an error.

- **No encryption, no split archives, no data descriptors**: The parser expects simple single-disk ZIP files with no encryption. Data descriptor records (bit 3 of flags) are not handled.

### 14.6 Coding Style and Exports

Unlike all other JS module files, ziputil.js uses `var` declarations throughout (not `const`/`let`). This is a stylistic difference from the rest of the codebase.

The file does NOT have a `module.exports` guard. The functions `crc32`, `parseZip`, and `createZip` are declared in global scope and are available as globals in both browser and Node.js environments. All other JS modules (g4enc.js, imageprocessing.js, pdfgen.js, jbig2pdf.js, jbig2-wrapper.js, pdfcompress.js) use the `if (typeof module !== 'undefined') module.exports = {...}` pattern (see section 9.7).

---

## 15. State Machine

```
EMPTY → FILE_LOADED → CONVERTING → RESULT / CANCELLED / ERROR_RECOVERY
```

### EMPTY (initial)
- `selectedFile = null`, `progressBoxState = null`
- Compress button disabled, shows "Choose PDF File"

### FILE_LOADED
- `selectedFile` set, `totalPageCount` known
- Compress button enabled (unless errors or RAM limit exceeded without override)
- AI/refresh box shown: AI button if form at defaults, refresh icon if form modified, nothing if file too heavy for even 144 DPI

### CONVERTING
- `conversionInProgress = true`, controls disabled
- Manual: `body.converting` class; AI: `body.ai-running` class
- Pre-conversion: `deepCleanMemory()` frees all prior results, zeros canvases, reinitializes JBIG2 WASM
- Compress button clickable for cancellation

### RESULT
- `progressBoxState = 'result'`, `window.resultPDF` set
- Shows size comparison, save button, Advanced Tricks
- Color-coded: green (<60% ratio), yellow (60-100%), orange (>100%)
- Save button grayed out if form settings changed from result settings (`validateFormMatchesResult`)

### CANCELLED
- `progressBoxState = 'cancelled'`
- Shows Advanced Tricks section (collapsed)

### ERROR_RECOVERY
- `recoverFromError()` saves settings, replays handleFileSelected, restores form → back to FILE_LOADED

---

## 16. Memory Management

### 16.1 RAM Estimation

```javascript
function estimateRAMBytes(numPages, dpi, pageSize, useJBIG2, fileSizeBytes) {
    base = fileSizeBytes * 2 + 150 MB
    renderPeak = width * height * 16  // canvas RGBA + imageData + processImage + headroom
    G4:   base + renderPeak + numPages * 200 KB
    JBIG2: base + renderPeak + bilevelPerPage * numPages * 2.5 + numPages * 800 KB
}
```

### 16.2 RAM Limit

Default: 500 MB. Memory tier 1 devices: 350 MB.

### 16.3 DPI Auto-Adjustment

When a file is opened:
1. If 310 DPI fits within RAM_LIMIT: keep Standard DPI.
2. Otherwise: binary-search for the highest DPI that fits, switch to Custom mode.

### 16.4 Pre-Conversion Cleanup

`deepCleanMemory()` runs before every conversion:
1. Nulls `window.resultPDF` and all result globals.
2. Zeros canvas backing stores (`canvas.width = 0; canvas.height = 0`).
3. Destroys and reinitializes JBIG2 WASM module (fresh heap).
4. Clears the progress div (frees Advanced Tricks DOM tree).
5. Hints GC (`window.gc()` if available).

### 16.5 Tier 1/2 Memory Freeing

On low-memory devices (`isLowMemoryTier = tier <= 2`):
- `pdfData` (the input ArrayBuffer) is nulled after `renderPDFPages` returns.
- In ZIP mode, `arrayBuffer` and `allEntries` are nulled after filtering, and `entry.data` is nulled after each entry's rendering.
- During save, `selectedFile` and all metadata globals are nulled before `endSave()`.
- This means the user cannot recompress without re-reading the file. State preservation handles re-reading via the Android URI.

### 16.6 File Size Guard

`fileSizeOver = inputFileSize > 175 MB` — fast early-out check redundant with the RAM formula but provides immediate feedback.

---

## 17. AI Auto-Setter

The "AI" button is a for-loop with a gradient background. It does not use artificial intelligence, machine learning, or neural networks. The ironic quotation marks are load-bearing.

### 17.1 Trial Generation

1. Detect page format: opens the file (or the first PDF in a ZIP), gets the first page's viewport at scale 1.0, computes its aspect ratio (`width/height`), and picks the format whose standard aspect ratio is closest. Standard ratios: A4 portrait (595.28/841.89), A4 landscape (841.89/595.28), Letter portrait (612/792), Letter landscape (792/612), Legal portrait (612/1008). Sets the page size radio button to the detected format.
2. Compute max safe DPI for this file.
3. Generate DPI levels from standard tiers (310, 250, 216) and lower if needed.
4. For each DPI level, generate trials:
   - Dithered G4 (at all DPI levels)
   - Dithered JBIG2 t=0.97 (at highest DPI only)
   - Dithered JBIG2 t=0.85 (at all DPI levels)
   - Undithered G4 (at lowest DPI only)
   - Undithered JBIG2 t=0.85 (at lowest DPI only)
5. Filter out trials that exceed RAM_LIMIT or JBIG2 feasibility limits.

### 17.2 Execution

For each runnable trial:
1. Set form controls to match trial settings.
2. Run `convertPDF()` or `convertZIP()`.
3. Track the best (smallest) result.
4. Stop early if compression ratio < 60%.
5. Clean intermediate state between trials.

### 17.3 Progress Tracking

The progress bar and ETA use:
- A MutationObserver on `progressText` to extract intra-trial progress from text like "Rendering page 3 of 10" or "FlateDecode compression: stream 5 / 12".
- Phase weights: G4 trials spend 70% in rendering, 15% post-processing, 15% FlateDecode. JBIG2 trials: 35% rendering, 50% encoding, 15% FlateDecode.
- EMA smoothing with τ=2s for display, τ=8s for rate estimation, τ=10s for ETA.
- Bootstrap period (6 seconds) blends a synthetic exponential curve with real data.
- Time-based asymptotic interpolation for the JBIG2 encoding phase (which reports no page-level progress).

### 17.4 Visual Elements

- Sparkle particles (CSS keyframe animations).
- Four-point star shapes.
- Two SVG unicorns (mirrored) with pink mane and golden horn.
- Rainbow arcs (SVG bezier curves with stroke-dashoffset animation).
- Lucky rainbow: plays randomly every 0-5 minutes.
- Happy rainbow: plays randomly every 0-1 minute.
- Progress bar with smooth CSS transform.
- After successful compression: fabulous save button with sparkles and a win banner.

### 17.5 Refresh Button

If the user changes any form control after file selection, the AI button is replaced by a plain refresh icon that resets form to defaults and re-shows the AI button.

---

## 18. Intro Animation

File: `intro.js` (428 lines)

A 6-step animated tutorial (steps 0–5) that runs on every fresh page load to demonstrate the app's workflow. Exported as `window.IntroAnimation` for use by the main application logic.

### 18.1 Object State

```javascript
const IntroAnimation = {
    isRunning: false,            // True while animation is playing
    isCancelled: false,          // Set by cancel(), checked between steps
    animationSpeed: 3,           // Base speed multiplier (3 = 3x faster than nominal)
    offlineSpeedMultiplier: 1,   // Additional multiplier for step 0
    demoSpeedMultiplier: 1,      // Additional multiplier for steps 1-5
};
```

### 18.2 Entry Point

**`start(offlineSpeed = 1, demoSpeed = 1)`** — async method. Called from the DOMContentLoaded handler (fresh load) or from the help button handler (replay). Returns early if already running.

1. Sets `isRunning = true`, `isCancelled = false`, stores speed multipliers.
2. Removes `intro-mode-loading` from `<html>` (makes container eligible to appear).
3. Calls `setupCloseButton()` — transforms the help button from "?" to "×" (Unicode `×`), sets `z-index: 200000` (above the overlay), changes `aria-label` to "Stop demo", attaches a click handler that calls `cancel()`.
4. Calls `createDemoOverlay()`.
5. Runs steps 0–5 sequentially, checking `isCancelled` between each.
6. Sets `isRunning = false` on completion.

The help button replays the animation with `IntroAnimation.start(0.1, 0.16)` — 10× slower offline prelude, 6.25× slower demo.

### 18.3 Speed and Timing

**`wait(ms, isOfflineStep = false)`** — returns a Promise that resolves after `ms / animationSpeed / speedMultiplier` milliseconds:

```javascript
const speedMultiplier = isOfflineStep ? this.offlineSpeedMultiplier : this.demoSpeedMultiplier;
return new Promise(resolve => setTimeout(resolve, ms / this.animationSpeed / speedMultiplier));
```

If `isCancelled` is true, returns `Promise.resolve()` immediately (no delay).

At default speed (`animationSpeed=3`, both multipliers=1), `wait(600, true)` resolves after 200 ms. At replay speed (0.1, 0.16), `wait(600, true)` resolves after `600 / 3 / 0.1` = 2000 ms.

### 18.4 Overlay DOM Structure

`createDemoOverlay()` creates a transparent overlay on top of the real UI:

```html
<div id="introOverlay" class="intro-overlay" aria-hidden="true">
    <div class="intro-container" id="introContainer">
        <div class="intro-upload-area">
            <div class="intro-choose-btn" id="introChooseBtn">{chooseFile}</div>
        </div>
        <div class="intro-compress-btn intro-disabled" id="introCompressBtn">{compressButton}</div>
    </div>
</div>
```

Button text is localized via `TRANSLATIONS[currentLang]` (with English fallback). The overlay is appended to `document.body` and made visible via `.visible` class.

### 18.5 Step 0 — Offline Privacy Message

Creates a `.intro-offline-message` div containing:

**SVG icon** (`class="intro-cloud-icon"`, viewBox `0 0 100 80`): Identical to the privacy icon (section 6.2.5) — globe, cloud, WiFi arcs — but the red cross uses animated `stroke-dasharray`/`stroke-dashoffset`:

```html
<line id="introCrossLine1" x1="20" y1="20" x2="80" y2="65"
      stroke="#e74c3c" stroke-width="6" stroke-linecap="round"
      stroke-dasharray="78" stroke-dashoffset="78"/>
<line id="introCrossLine2" x1="80" y1="20" x2="20" y2="65" ... />
```

Both lines start fully hidden (`dashoffset=78` = fully retracted). JavaScript sets `style.strokeDashoffset = '0'` with a CSS `transition` to animate them drawing in.

**Privacy text**: `<p class="intro-privacy-text">{privacyNotice}</p>` — localized.

**Timing** (at default speed):

| Wait call | Nominal ms | Actual ms | What happens before |
|---|---|---|---|
| `wait(600, true)` | 600 | 200 | Message fades in |
| `wait(600, true)` | 600 | 200 | First cross line draws (transition duration `0.2 / offlineSpeedMultiplier` s) |
| `wait(600, true)` | 600 | 200 | Second cross line draws |
| `wait(600, true)` | 600 | 200 | Message fades out, container fades in |

Total offline prelude: ~800 ms at default speed. Message is then removed from DOM.

### 18.6 Step 1 — Choose PDF File

1. Depresses the choose button (`introChooseBtn.classList.add('intro-depressed')`). Wait 200 ms.
2. Creates a PDF icon via `createPDFIcon('large')` (see section 18.10). Sets `id="introPDFIcon"`.
3. Positions the icon centered on the choose button using `getBoundingClientRect()` (absolute pixel coordinates).
4. Appends to the overlay, animates in via `.visible` class. Wait 800 ms.
5. Releases the button (removes `.intro-depressed`). Wait 300 ms.

### 18.7 Step 2 — Move to Compress

1. Enables the compress button (removes `.intro-disabled`).
2. Moves the PDF icon to the compress button (updates `style.left`/`style.top` — CSS `transition` animates the movement). Wait 800 ms.
3. Depresses the compress button. Wait 200 ms.
4. Shrinks the icon: removes `.size-large`, adds `.size-small` (CSS transitions the size change, representing compression). Wait 400 ms.

### 18.8 Step 3 — Show Result

1. Creates a `.intro-result` div with a `.intro-result-content` containing a `.intro-size-change` span.
2. **RTL handling**: For RTL languages (`ar`, `he`, `ur`, `yi`), the text `1 MB → 80 kB` is wrapped in `<span dir="ltr">` to prevent the arrow direction from reversing. For LTR languages, the text is used directly.
3. Appends result to the container, animates in. Wait 50+400 ms.
4. Creates a `.intro-save-btn` with localized text (`resultSaveButton`). Appends to the result, animates in. Wait 50+600 ms.
5. Releases the compress button. Wait 200 ms.

### 18.9 Step 4 — Move to Save

1. Moves the PDF icon to the save button position. Wait 600 ms.
2. Depresses the save button, fades out the icon (`.fading` class). Wait 800 ms.

### 18.10 Step 5 — Exit

1. Removes `intro-mode-loading` from `<html>` (second removal, for safety — already removed in `start()`).
2. Adds `.intro-fading-out` to the overlay (CSS transition fades it out). Wait 800 ms.
3. Removes the overlay from DOM.
4. Removes `fe-intro-active` from `<body>` (restores Flat Earth background to normal z-index).
5. Removes any remaining PDF icon.
6. Calls `restoreHelpButton()` — reverts "×" back to "?", removes z-index override, detaches cancel handler.
7. Sets `isRunning = false`.

### 18.11 PDF Icon SVG

`createPDFIcon(size)` creates a `div.intro-pdf-icon.size-{size}` containing an inline SVG (`viewBox="0 0 64 80"`):

- **Document body**: path `M 4 0 L 40 0 L 60 20 L 60 80 L 4 80 Z`, filled `#E74C3C` (red), stroked `#C0392B`.
- **Folded corner**: triangle `M 40 0 L 40 20 L 60 20 Z`, filled `#C0392B` (darker red).
- **Text lines**: three white rectangles at y=30, y=38, y=46 (widths 40, 40, 30), opacity 0.8.
- **"PDF" label**: `<text x=32 y=68>` centered, white, bold, 16px Arial.

The `.size-large` and `.size-small` CSS classes control the icon dimensions. Transitioning between them (step 2) animates a "shrinking" effect representing compression.

### 18.12 Cancellation

`cancel()` — called by the close button handler. Sets `isCancelled = true`, immediately removes the overlay and PDF icon from DOM, removes `fe-intro-active` from body, calls `restoreHelpButton()`, sets `isRunning = false`. The async `start()` method checks `isCancelled` between every step and returns early.

### 18.13 Skipping on State Restoration

On state restoration (Android WebView restart, OOM recovery, bfcache), the `DOMContentLoaded` handler detects `_lastKnownState` is set and takes the restore branch, which does NOT call `IntroAnimation.start()`. The `intro-mode-loading` class is never added (or is immediately removed by `restoreAppState()`), so the container is visible without any animation.

---

## 19. Easter Eggs and Humor

### 19.1 Flat Earth Background

Files: `flatearth.js` (270 lines), `flatearth-paths.json`

Activated when locale ends with `-FE` (en-FE, cs-FE, sk-FE) or on April 1st for en/cs/sk users.

Renders a CSS 3D flat earth disc behind the main content with:
- A circular disc with an isometric-style 3D projection.
- SVG continent paths from flatearth-paths.json (121 paths).
- A particle waterfall effect through a starfield using canvas.
- The disc is placed in the `.fe-bg` div positioned behind the main container.

Functions: `feInit()` starts the animation, `feStop()` stops it. `feStop()` cancels the animation frame, clears particle/disc arrays, and empties the `.fe-bg` container div.

#### 19.1.1 flatearth-paths.json Data Format

A JSON array of 121 SVG path `d`-attribute strings representing continent and island outlines on the flat earth disc. Each string is a closed polygon using only three SVG path commands:

- `M x,y` — Move to (start a new sub-path)
- `L x,y` — Line to (draw a straight line segment)
- `Z` — Close path (connect back to the `M` point)

No curves (`Q`, `C`, `A`) are used — all shapes are polygonal approximations.

**Coordinate system**: All coordinates are in the range ~15.6 to ~83.5, within a 0–100 unit space. This matches the `viewBox="0 0 100 100"` of the world map SVG created by `feCreateWorldSVG()` (section 42.1.3). The center of the disc at coordinate (50, 50) corresponds to the North Pole.

**Projection**: Azimuthal equidistant projection centered on the North Pole. In this projection:
- The North Pole is at the center (50, 50).
- Latitude lines are concentric circles (equidistant spacing from center).
- Longitude lines are straight radial lines from center.
- Antarctica forms the outer boundary (the "ice wall" in flat earth terminology).
- Continents near the equator appear stretched horizontally.

This is the standard map projection used by flat earth proponents and is also used on the United Nations flag.

**Data statistics**: 121 paths, ~11 KB total. Shortest path: 45 characters (small island). Longest path: 540 characters (large continent outline). Average: 92 characters per path. Paths contain ~2,000 coordinate values total.

The data is stored in a separate JSON file (not inline in flatearth.js) because the paths are data, not code. At build time, `build.py` injects them into the `FE_LAND_PATHS` array in flatearth.js by replacing the `FLATEARTH_PATHS_PLACEHOLDER` token (section 3.1 step 5).

### 19.2 Flat Earth Translations

Each FE locale has translations reworded with flat earth terminology:
- en-FE: References to the "dome," "ice wall," "firmament plane"
- cs-FE: Czech with flat earth dome/plane references
- sk-FE: Slovak with firmament/ice wall references

### 19.3 Gen-Z / Internet Slang Locale (67)

Locale code `67` provides translations in internet slang: "no cap," "fr fr," "bussin," etc.

### 19.4 Joke Locale Visibility

Joke locales (FE variants, 67) are hidden in the language selector unless:
- It is April 1st, OR
- The GitHub corner is visible (which happens when any modal is opened in the Android app, or always in the browser)

### 19.5 The "AI" Button

The name "AI" is in ironic quotation marks. The About modal contains a detailed explanation of what the button does and does not do. The closing line of the About section on this topic: "The ironic quotation marks around 'AI' are load-bearing."

The About modal also contains: "What you are looking at is, technically speaking, a clown-grade implementation of control engineering... A disturbing amount of what gets sold as 'AI' in the real world is control engineering with a marketing department."

### 19.6 RAM Override Label

When the RAM override checkbox is shown (document exceeds RAM limit), the label includes:
- A formatted RAM estimate
- A string of emojis: 🔥💻⚡️⚠️ 💥 🐕☕🔥 ¯\_(ツ)_/¯
- An inline SVG nuclear explosion mushroom cloud icon
- A zero-width 🍄 (mushroom emoji, invisible)
- 😎
- When checked, appended italic text: "(my device can run out of memory or run hot, the application might crash, and I accept that risk...)"

### 19.7 About Modal Humor

- Opening quote: "We were so preoccupied with whether we could, we didn't stop to think if we should."
- Architecture section titled "A Study in Questionable Decisions"
- ASCII art showing nested HTML structure described as "like a turducken, but for web apps"
- "Source code may contain nuts (and tarballs)"
- Disclaimer: "The absurdity is purely architectural. Use responsibly, or don't. We're not your supervisor."
- "Generated with Claude on April 1, 2026"

### 19.8 Self-Download Description

In the About modal: "Yes, you can download this entire app as a standalone HTML file. It's like looking in a mirror that's also a photocopier."

---

## 20. Android Wrapper

File: `build-apk.sh` (Java code as heredoc, lines 140-1094)

### 20.1 Activity Configuration

- `configChanges="orientation|screenSize|keyboardHidden"` — Activity is NOT recreated on rotation. Instance variables survive configuration changes.
- No internet permission declared.
- `android:allowBackup="false"`
- `android:hardwareAccelerated="true"`
- `FLAG_KEEP_SCREEN_ON` set during processing.

### 20.2 WebView Setup

`setupWebView()` creates the WebView, sets it as the content view, and configures it:

```java
settings.setJavaScriptEnabled(true);
settings.setDomStorageEnabled(true);
settings.setAllowFileAccess(true);
settings.setAllowContentAccess(true);
settings.setDatabaseEnabled(true);
settings.setCacheMode(WebSettings.LOAD_DEFAULT);
settings.setBuiltInZoomControls(true);
settings.setDisplayZoomControls(false);
```

**External URL handling** (`WebViewClient.shouldOverrideUrlLoading`): URLs starting with `http://` or `https://` are opened in the system browser via `Intent(ACTION_VIEW)` with `Intent.FLAG_ACTIVITY_NEW_TASK`. If `startActivity()` throws (no browser installed), a `"Cannot open browser"` Toast is shown. All other URLs (including `file:///android_asset/`) load normally in the WebView.

**Renderer crash recovery** (`WebViewClient.onRenderProcessGone`): If the WebView renderer is killed by the OS (OOM), the callback destroys the dead WebView, sets `skipIntroOnReload = true`, calls `setupWebView()` to create a fresh WebView, resets `modalIsOpen = false`, and loads `index.html`. The state restoration path (section 23) then restores the user's form state and file.

**File chooser** (`WebChromeClient.onShowFileChooser`): Launches `fileChooserLauncher` with `ACTION_OPEN_DOCUMENT` (see section 20.5).

**JavaScript interfaces registered**: inner class `FileHandler` registered as `"AndroidFileHandler"` and inner class `ModalStateHandler` registered as `"AndroidModalState"` (see section 20.3).

### 20.3 JavaScript Interfaces

Two inner classes are registered as JavaScript interfaces:

#### 20.3.1 `FileHandler` (registered as `"AndroidFileHandler"`)

**Save methods (chunked streaming to temp file):**

- **`beginSave(filename, mimeType)`** — Stores filename and MIME type, nulls `pendingFileData`, cleans up any leftover temp files, and creates a new temp file via `File.createTempFile("pdf_save_", ".tmp", getCacheDir())`. The `"pdf_save_"` prefix is used by `cleanupTempFiles()` on startup to delete orphaned files.

- **`writeChunk(base64Chunk)`** — If `pendingTempFile` is non-null: decodes the base64 string via `Base64.decode(base64Chunk, Base64.DEFAULT)` and appends to the temp file using `new FileOutputStream(pendingTempFile, true)` (the `true` flag opens for append). Each chunk is ~768 KB of binary data (1 MB base64). If the temp file is null (beginSave failed), the call is silently ignored.

- **`endSave()`** — If temp file and filename are set, runs the SAF save dialog **on the UI thread** (`runOnUiThread()`). On tier 1/2 devices (`memoryTier <= 2`): sets `webViewKilledForSave = true`, destroys the WebView (`webView.destroy(); webView = null`), and replaces the content view with an empty View to free memory before the SAF dialog appears. Then launches `fileSaverLauncher` with `ACTION_CREATE_DOCUMENT`, `CATEGORY_OPENABLE`, the pending MIME type and filename, and `EXTRA_INITIAL_URI` set to `content://com.android.externalstorage.documents/document/primary:Download` (points to the Downloads folder).

- **`saveFile(filename, base64Data, mimeType)`** — Convenience method that calls `beginSave(filename, mimeType)`, `writeChunk(base64Data)`, `endSave()` sequentially. Used for small saves (source tarball download, self-download) where the data fits in a single chunk. Reuses the same temp-file streaming path — does NOT hold data in memory.

**File saver result callback** (`fileSaverLauncher`):

On success (`RESULT_OK`): Opens an `OutputStream` to the user-selected URI. Reads from `pendingTempFile` (primary path) using a 65536-byte buffer in a read loop, or from `pendingFileData` (fallback, currently unused) via a single `write()`. Shows `"File saved: {filename}"` Toast. In the `finally` block: nulls `pendingFileData`, `pendingFilename`, `pendingMimeType`, calls `cleanupTempFiles()`, and if `webViewKilledForSave` is true, calls `showSaveResultAnimation(true)`.

On cancel/failure: calls `cleanupTempFiles()`, and if `webViewKilledForSave` is true, calls `showSaveResultAnimation(false)` (the animation still plays but shows a failure X mark).

**State management methods:**

- **`saveFormState(json)`** — Stores the JSON string in the `savedFormStateJson` instance variable.
- **`saveInputFileMeta(filename, fileSize, isZip)`** — Stores file metadata in instance variables.
- **`getMemoryTier()`** — Returns `memoryTier` (1, 2, or 3).

**State restoration methods:**

- **`hasRestoredState()`** → boolean — Returns `true` only when all three conditions are met: `skipIntroOnReload` is true, `savedFormStateJson` is non-null, and `savedInputFileUri` is non-null.
- **`getRestoredFormState()`**, **`getRestoredFileName()`**, **`getRestoredFileSize()`**, **`getRestoredIsZipMode()`** — Getters for saved state instance variables.
- **`prepareRestoredFile()`** → boolean — Reads the file from `savedInputFileUri` into `restoredFileBytes` (a `byte[]`). Opens an `InputStream` via `getContentResolver().openInputStream()`, reads in 65536-byte chunks into a `ByteArrayOutputStream`, then converts to `byte[]` via `toByteArray()`. Returns `true` on success, `false` if the URI is null or reading fails (with `restoredFileBytes` set to null).
- **`getRestoredFileLength()`** → int — Returns `restoredFileBytes.length` or 0 if null.
- **`readRestoredFileChunk(offset, length)`** → String — Extracts a slice of `restoredFileBytes` via `Arrays.copyOfRange(restoredFileBytes, offset, end)` where `end = Math.min(offset + length, restoredFileBytes.length)`. Base64-encodes the slice with `Base64.encodeToString(..., Base64.NO_WRAP)`. The `NO_WRAP` flag suppresses line breaks in the output (the JS side would misparse them).
- **`clearRestoredFile()`** — Sets `restoredFileBytes = null` to free the Java-side byte array after the JS side has finished chunked reading.

#### 20.3.2 `AndroidModalState` (registered as `"AndroidModalState"`)

- **`setModalOpen(boolean)`** — Sets the `modalIsOpen` instance variable. Used by the back button handler (section 20.4) to determine whether to close modals or navigate back.

### 20.4 Back Button Handling

Uses `OnBackPressedCallback`:
1. If probing: ignore (return immediately).
2. If `modalIsOpen` is true and WebView exists: inject JavaScript via `webView.evaluateJavascript()` to close modals, then set `modalIsOpen = false`.
3. If WebView can go back: `webView.goBack()`.
4. Otherwise: disable the callback and dispatch to the system default (exits the app).

**Injected JavaScript** (step 2): An IIFE that gets all four modals by ID and removes the `show` class from each:

```javascript
(function() {
    var aboutModal = document.getElementById('aboutModal');
    var licenseModal = document.getElementById('licenseModal');
    var languageModal = document.getElementById('languageModal');
    var privacyModal = document.getElementById('privacyModal');
    if (aboutModal && aboutModal.classList.contains('show')) aboutModal.classList.remove('show');
    if (licenseModal && licenseModal.classList.contains('show')) licenseModal.classList.remove('show');
    if (languageModal && languageModal.classList.contains('show')) languageModal.classList.remove('show');
    if (privacyModal && privacyModal.classList.contains('show')) privacyModal.classList.remove('show');
})()
```

### 20.5 File Picker

Uses `ACTION_OPEN_DOCUMENT` (not `ACTION_GET_CONTENT`) with `intent.setType("*/*")` and `EXTRA_MIME_TYPES` array `["application/pdf", "application/zip"]`. Adds `Intent.CATEGORY_OPENABLE`. Takes persistable URI permission on the selected file for re-reading after WebView restart (with `SecurityException` catch around the persistable permission call).

### 20.6 File Saver

Uses `ACTION_CREATE_DOCUMENT` with `EXTRA_INITIAL_URI` pointing to the Downloads folder (see section 20.3.1 `endSave()` for full details). Reads from the temp file and writes to the selected URI. Shows a Toast on success.

On tier 1/2 devices, the WebView is destroyed before showing the SAF dialog to free memory. After the save completes (success or cancel), `showSaveResultAnimation()` plays a 4-second animation, then `recreateWebView()` restores the app.

#### 20.6.1 Save Result Animation

`showSaveResultAnimation(boolean success)` creates a separate WebView with `setJavaScriptEnabled(false)` and a white background. It loads a minimal inline HTML page containing an SVG diskette icon with an animated result indicator:

**Diskette SVG** (viewBox `0 0 100 100`):
- Body: `<rect x=10 y=10 w=80 h=80 rx=4>` filled `#607D8B` (blue-grey), stroked `#455A64`
- Metal slider: `<rect x=30 y=10 w=30 h=25 rx=2>` filled `#B0BEC5` (light grey), with a window `<rect x=40 y=13 w=10 h=19>` filled `#607D8B`
- Label area: `<rect x=20 y=50 w=60 h=35 rx=2>` filled `#ECEFF1` (off-white)
- Download arrow on label: `<path>` with stroke `#455A64`, width 3, round caps/joins

**Result indicator** (overlaid on the diskette):
- Success: green (`#4CAF50`) checkmark path `M 20,50 L 40,70 L 75,25`
- Failure: red (`#F44336`) X path `M 25,25 L 75,75 M 75,25 L 25,75`
- Both use `stroke-width="8"`, round caps/joins, and CSS `stroke-dasharray: 150; stroke-dashoffset: 150` with a `draw` animation: `0.8s ease-out 0.5s forwards` (0.5s delay, then 0.8s draw-in).

**Sizing**: `width: 70vmin; height: 70vmin; max-width: 400px; max-height: 400px`.

**Duration**: A `Handler.postDelayed()` callback destroys the animation WebView after 4000 ms, then calls `recreateWebView()`.

#### 20.6.2 `recreateWebView()`

Called after save animation completes, or directly after `onRenderProcessGone`:

1. If an existing `webView` is non-null, destroys it.
2. Sets `skipIntroOnReload = true` (so the new page load triggers state restoration instead of the intro animation).
3. Calls `setupWebView()` (creates a fresh WebView with all settings and interfaces).
4. Sets `modalIsOpen = false`.
5. Loads `file:///android_asset/index.html`.

The new page load will detect `hasRestoredState() === true` and run the full state restoration path (section 23).

#### 20.6.3 `onDestroy()`

```java
@Override
protected void onDestroy() {
    cleanupTempFiles();
    if (webView != null) {
        webView.destroy();
    }
    super.onDestroy();
}
```

Ensures temp files (any `pdf_save_*` files in the cache directory) are deleted and the WebView is properly destroyed when the Activity is finishing.

### 20.7 Themes

Four theme variants for WebView `prefers-color-scheme` detection:
- `values/styles.xml`: Light theme (default)
- `values-night/styles.xml`: Dark theme
- `values-v35/styles.xml`: API 35 light theme with `windowOptOutEdgeToEdgeEnforcement`
- `values-night-v35/styles.xml`: API 35 dark theme with `windowOptOutEdgeToEdgeEnforcement`

---

## 21. Memory Probe System

On each launch (until the full probe has been run and its result persisted), the app determines the device's memory tier through a calibration process.

### 21.1 Quick Detection

Uses `ActivityManager.MemoryInfo.availMem`:
- ≥2000 MB → tier 3
- ≥800 MB → tier 2
- <800 MB → tier 1

If the value is between 100 MB and 4 TB, it is used for the current session only — nothing is written to SharedPreferences, so the state stays `"none"` and the quick check runs again on next launch. The full stress-test probe is never triggered in this path.

### 21.2 Full Probe (fallback)

If `availMem` is out of range or unavailable, a full stress-test probe is run. All Activity-level logging uses `TAG = "MemProbe"`.

#### 21.2.1 Runtime State Fields

| Field | Type | Purpose |
|---|---|---|
| `probing` | `boolean` | True while any probe is running. Used to suppress back button. |
| `probeRendererDied` | `boolean` | Set by `onRenderProcessGone`. Indicates WebView renderer was killed. |
| `probeJavaFailed` | `boolean` | Set by `allocateSacrificialMemory()` on OOM/interrupt/stop. |
| `probeTrimMemoryFired` | `boolean` | Set by `onTrimMemory(RUNNING_CRITICAL)`. |
| `sacrificialData` | `byte[][]` | Array of 1 MB Java heap blocks. Nulled to free memory. |
| `sacrificialThread` | `volatile Thread` | Background thread running `allocateSacrificialMemory()`. |
| `sacrificialStop` | `volatile boolean` | Signals sacrificial thread to abort. |
| `probeHandler` | `Handler` | Main-looper handler for scheduling phase transitions. |
| `probeId` | `int` | Monotonically increasing guard. Incremented on each new probe. All delayed callbacks compare their captured `id` to `probeId` and return early if mismatched, preventing stale callbacks from acting on a new probe. |
| `probeTimerStarted` | `boolean` | Set when `ProbeSignal.ready()` fires. Prevents duplicate phase 1 starts. |

#### 21.2.2 State Machine

Persisted in SharedPreferences (`"mem_probe"`), committed synchronously via `.commit()` (not `.apply()` — must survive a crash during the probe):

```
"none" → "testing_1400" → "testing_800" → "done"
```

**`startMemoryProbe()` entry logic:**

- State is `"testing_1400"`: App was killed during the 1400 MB probe. Record failure, set state to `"testing_800"`, run 800 MB probe (pink spinner `0xFFFF69B4`).
- State is `"testing_800"`: App was killed during the 800 MB probe. Both tests failed → save tier 1.
- State is `"none"`: Fresh start. Try quick detection first (`getAvailableMemoryMB()`). If `availMem` is in the sane range 100 MB to 4 TB (`4 * 1024 * 1024` MB): set `memoryTier` in memory and call `loadMainApp()` immediately — **nothing is written to SharedPreferences**, so the state remains `"none"` and the quick check reruns on every launch until the full probe is triggered. Otherwise: set state to `"testing_1400"`, run 1400 MB probe (purple spinner `0xFF764BA2`).

#### 21.2.3 Probe HTML and ProbeSignal Interface

**`makeProbeHtml(int megabytes)`** generates the HTML loaded into the probe WebView:

1. Calls `ProbeSignal.ready()` via the registered JavaScript interface (if available — guarded by `typeof ProbeSignal !== 'undefined'`).
2. Allocates `megabytes` `Uint32Array`s, each with 262144 entries (1 MB per array). Elements are filled with `(Math.random()*4294967296) ^ (Math.random()*4294967296)` (XOR of two random 32-bit values).
3. A read-back function `rd()` runs every 500 ms via `setTimeout`. It reads one value from every 512th position in every array (summing them with `(v + d[c][i]) | 0`), keeping the pages touched so the OS cannot swap them out. A `<span id="v">` shows a `.` or `,` based on the parity of the accumulated value (cosmetic, proves JS is alive).

**`ProbeSignalInterface`** is an inner class registered as `"ProbeSignal"` on the probe WebView:

```java
public class ProbeSignalInterface {
    @JavascriptInterface
    public void ready() {
        final int id = probeId;
        runOnUiThread(() -> {
            if (id != probeId || probeTimerStarted) return;
            probeTimerStarted = true;
            probeHandler.postDelayed(() -> {
                if (id != probeId) return;
                onPhase1Done(id);
            }, 8000);
        });
    }
}
```

When JS calls `ProbeSignal.ready()`, the handler schedules `onPhase1Done()` after 8000 ms (phase 1 duration). The `probeId` guard ensures that a `ready()` signal from a previous (destroyed) probe WebView is ignored. `probeTimerStarted` prevents duplicate phase 1 starts if `ready()` is called multiple times.

**60-second fallback**: `runProbe()` also schedules a safety timer: if `ready()` is never called within 60000 ms (JS failed to load or execute), the probe is treated as failed (`probeRendererDied = true`, then `onPhase2Done()`).

#### 21.2.4 `runProbe(megabytes, spinnerColor)`

1. Increments `probeId`, resets all failure flags and `probeTimerStarted`.
2. Calls `ensureCalibrationScreen(spinnerColor)` to show or update the calibration UI.
3. Creates a new WebView and adds it to the `probeFrame` at index 0 (behind the calibration screen — not visible to the user).
4. Enables JavaScript, registers `ProbeSignalInterface` as `"ProbeSignal"`.
5. Sets an `onRenderProcessGone` handler that sets `probeRendererDied = true` and, if phase 2 is already running, aborts it immediately (removes pending callbacks, frees sacrificial memory, schedules `onPhase2Done()` after 2 seconds).
6. Loads the probe HTML via `webView.loadDataWithBaseURL()`.
7. Schedules the 60-second fallback timeout.

#### 21.2.5 Phase 1 and Phase 2

**`onPhase1Done(id)`**: If the renderer already died during phase 1, skips to `onPhase2Done()` after 2 seconds. Otherwise, starts phase 2:

1. Enlarges the spinner from 120×120 px to 180×180 px (visual indicator of increased stress). Note: these are raw pixel values passed to `FrameLayout.LayoutParams`, not dp — no density-independent conversion is performed.
2. Starts a background thread at `THREAD_PRIORITY_BACKGROUND` running `allocateSacrificialMemory()`.
3. Schedules `onPhase2Done()` after `PHASE2_DURATION_MS + 10000` ms (16 s allocation + 10 s hold = 26 s total).

**`allocateSacrificialMemory()`** (runs on background thread):

1. Computes target: `mb = (int)(Math.min(memoryClass, 256) * 0.8)` MB, where `memoryClass` comes from `ActivityManager`. Minimum 1 MB.
2. Computes pacing: `sleepPerMB = PHASE2_DURATION_MS / mb` — spreads allocation over 16 seconds.
3. Allocates `sacrificialData = new byte[mb][]`, then in a loop: allocates each 1 MB block via `new byte[1048576]`, fills with random data via `java.util.Random.nextBytes()`, and sleeps `sleepPerMB` ms between blocks.
4. **Abort conditions** checked before each allocation: `sacrificialStop` (set by `freeSacrificialMemory()`), `Thread.interrupted()`, or `probeTrimMemoryFired`. If triggered: sets `probeJavaFailed = true`, nulls `sacrificialData`, returns.
5. **Error handling**: Catches `Throwable` (not just `OutOfMemoryError`) — covers `OutOfMemoryError`, `InterruptedException`, and any unexpected error. Sets `probeJavaFailed = true`.

**`freeSacrificialMemory()`**:

1. Sets `sacrificialStop = true` to signal the allocation thread.
2. Nulls `sacrificialData` to release all heap blocks.
3. Interrupts the thread and joins with a 2-second timeout.

**`onTrimMemory(int level)`** (Activity override): If `probing` is true and `level >= TRIM_MEMORY_RUNNING_CRITICAL` (note: `>=` not `==` — higher levels are also critical), sets `probeTrimMemoryFired = true`, calls `freeSacrificialMemory()`, and destroys the probe WebView.

**`onPhase2Done()`**: Determines result: `failed = probeRendererDied || probeJavaFailed || probeTrimMemoryFired`. Frees all probe resources: `freeSacrificialMemory()`, removes WebView from `probeFrame` and destroys it, calls `System.gc()`, clears all pending handler callbacks, increments `probeId`, restarts the dot timer.

Then based on the persisted state:
- State `"testing_1400"` + failed: sets state to `"testing_800"`, shows grey spinner, waits 5 seconds, then runs 800 MB probe (pink spinner).
- State `"testing_1400"` + passed: saves tier 3 via `saveMemoryTier(3)`.
- State `"testing_800"` + failed: saves tier 1.
- State `"testing_800"` + passed: saves tier 2.

#### 21.2.6 Post-Probe Transitions

**`saveMemoryTier(tier)`**: Saves tier to SharedPreferences (synchronous `.commit()`), sets state to `"done"`, sets `probing = false`, shows grey spinner, then waits 3 seconds (`Handler.postDelayed`) before calling `loadMainApp()`. The 3-second delay lets the OS reclaim memory freed from the probe. Used only after a full stress-test probe completes.

**`loadMainApp()`**: Stops the dot timer, clears `probeFrame` and `squareDots`, destroys the probe WebView if it still exists, then calls `setupWebView()` + `webView.loadUrl("file:///android_asset/index.html")`.

### 21.3 Visual Feedback During Probe

**`ensureCalibrationScreen(spinnerColor)`**: Creates (or reuses) a `FrameLayout` (`probeFrame`) that covers the screen with a white background. On first call, adds:

- A `TextView` at the top: text from `R.string.calibrating` ("First launch, calibrating…"), color `0xFF666666`, text size 16, centered horizontally, `topMargin = 80`.
- A `ProgressBar` (indeterminate spinner): 120×120 px (raw pixel `LayoutParams`, not dp-converted), centered. Color set via `getIndeterminateDrawable().setColorFilter(color, PorterDuff.Mode.SRC_IN)`.

On subsequent calls, only updates the spinner color (reuses the existing `probeFrame`).

**Spinner colors:**

| Phase | Color value | Visual |
|---|---|---|
| 1400 MB probe | `0xFF764BA2` | Purple (matches app gradient) |
| 800 MB probe | `0xFFFF69B4` | Hot pink |
| Transitions / delays | `0xFF888888` | Grey |

**Random dots** (`addRandomSquare`, `removeRandomDot`, `squareTick`): Cosmetic decoration during the calibration screen. A `Runnable` (`squareTick`) fires every 300 ms and adds a black dot at a random position on a 20-column × 50-row grid. Dot size is 30% of the cell size (minimum 2 px). Dots are positioned at cell centers via `col * cellW + (cellW - sqW) / 2`. When the dot count exceeds 60, a random existing dot is removed. The timer is started by `startSquareTimer()` (guarded by `squareTimerRunning` to prevent duplicates) and stopped by `stopSquareTimer()` which removes all pending callbacks.

### 21.4 Memory Tier Effects

| Tier | Available RAM | RAM_LIMIT | WebView killed on save | Input data freed |
|------|--------------|-----------|----------------------|-----------------|
| 1 | <800 MB | 350 MB | Yes | Yes |
| 2 | 800-2000 MB | 500 MB | Yes | Yes |
| 3 | ≥2000 MB | 500 MB | No | No |

---

## 22. Android File Handling

### 22.1 Chunked Save

The save path avoids holding the full base64 of the result in JS memory:

1. JS calls `beginSave(filename, mimeType)` → Java creates temp file.
2. JS loops over the data in 768 KB chunks, base64-encoding each and calling `writeChunk(base64)` → Java decodes and appends to temp file.
3. JS frees `window.resultPDF` and `data`.
4. JS calls `endSave()`.
5. Java (on UI thread): optionally destroys WebView (tier 1/2), shows SAF dialog.
6. User picks save location → Java streams from temp file to output URI.
7. Cleanup: delete temp file, restore WebView if needed.

### 22.2 Temp File Cleanup

On `onCreate()`, all files matching `pdf_save_*` in the cache directory are deleted. Also cleaned up after every save operation.

### 22.3 URI Permission Management

On fresh app start (`onCreate`), all persisted URI permissions are released via `releasePersistableUriPermission()`. This prevents accumulation of stale permissions from previous sessions.

When a file is selected via ACTION_OPEN_DOCUMENT, `takePersistableUriPermission()` is called to retain read access for file re-reading after WebView restart.

---

## 23. State Preservation Across WebView Kills

### 23.1 Triggers

Three events can require state restoration:
1. **Tier 1/2 save**: WebView is destroyed before showing SAF dialog, then recreated.
2. **OOM crash**: WebView renderer is killed by the OS, `onRenderProcessGone` fires.
3. **Browser bfcache**: Page is restored from back/forward cache.

### 23.2 Architecture

**Instance variables** (Java, NOT SharedPreferences — lost when process dies):
```java
private String savedFormStateJson = null;
private Uri savedInputFileUri = null;
private String savedInputFileName = null;
private long savedInputFileSize = 0;
private boolean savedIsZipMode = false;
private byte[] restoredFileBytes = null;
private boolean skipIntroOnReload = false;
```

**JS global** (outside DOMContentLoaded scope, survives bfcache):
```javascript
var _lastKnownState = null;  // { form: {...}, file: File|null, isZip: bool }
```

### 23.3 Save Path

`saveAppState()` is called from 8 locations:
1. Language switch (English checkbox change) — 1 call
2. Language switch (Mongolian checkbox change) — 1 call
3. `updateCompressButton()` — covers all form changes
4. `handleFileSelected()` — file selection + metadata
5. Compress button handler (before `deepCleanMemory()`)
6. AI auto-setter (before `deepCleanMemory()`)
7. `downloadFile()` (before `endSave()`)
8. `restoreAppState()` completion

The function:
1. Reads all form controls via `getCurrentFormState()` → `{ditherMode, pageRange, dpiMode, dpiValue, pageSize, useJBIG2, jbig2Threshold, preserveRotation, includeProducer, includeTimestamp, currentLang, useEnglish}`.
2. Updates `_lastKnownState.form` (and `.file` if a file is selected).
3. Calls `AndroidFileHandler.saveFormState(JSON.stringify(form))` if available.

File metadata is separately sent to Android via `AndroidFileHandler.saveInputFileMeta()` in `handleFileSelected()`.

### 23.4 Restore Path

**Android restore** (in DOMContentLoaded):
1. Check `AndroidFileHandler.hasRestoredState()`.
2. Get form state JSON and parse it.
3. Call `prepareRestoredFile()` to read file from URI into `restoredFileBytes`.
4. Read file in 768 KB base64 chunks, assemble into Uint8Array, create File object.
5. Call `clearRestoredFile()` to free Java-side byte array.
6. Set `_lastKnownState = { form, file, isZip }`.

**Unified restore** (`restoreAppState()`):
1. Remove `intro-mode-loading` class (prevents intro animation).
2. Restore language (English checkbox if saved).
3. Restore basic form controls (dither mode, DPI, page size).
4. Set `restoringState = true` (prevents `autoAdjustDPI()` from overriding restored DPI).
5. Call `handleFileSelected(file)` which resets `resultSettings`.
6. In `.then()` callback: set `restoringState = false`, repopulate `resultSettings` from saved form, build Advanced Tricks section via `buildAdvancedTricksHTML(false)`, attach listeners.
7. Show AI/refresh button, call `saveAppState()`.

**bfcache restore** (pageshow event):
```javascript
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        resetAppState();
        restoreAppState();  // uses _lastKnownState which survived bfcache
    }
});
```

### 23.5 Race Condition Prevention

The browser-restored-form detection (`setTimeout(100ms)` that checks for stale form values and resets) is placed in an `else` branch: it only runs when `_lastKnownState` is null. This structurally eliminates the race condition where the detection timer would fire after restore and reset the restored values.

### 23.6 `restoringState` Flag

Prevents `autoAdjustDPI()` from overriding the restored DPI. Set to `true` before `handleFileSelected()` during restore, set to `false` in the `.then()` callback.

---

## 24. Self-Extracting HTML Loader

### 24.1 Structure

The final HTML file has this structure:
```html
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <div class="loader">spinner + title + "Decompressing..."</div>
  <script>/* pako library */</script>
  <script>
    const COMPRESSED_HTML_BASE64 = '...';
    // Decode base64 → decompress with pako.inflate → document.write()
  </script>
</body>
</html>
```

### 24.2 Pristine HTML Preservation

Before `document.write()` replaces the page content, the loader saves a clean copy of itself for the self-download feature (section 25). The sequence is:

**Step 1 — Deep clone**: `const pristineDOM = document.documentElement.cloneNode(true)` — clones the entire `<html>` element including all children. This captures the loader HTML as it exists in the DOM at this moment.

**Step 2 — Extension pollution removal**: Browser extensions (particularly Dark Reader) inject elements into the DOM. Two `querySelectorAll` calls remove them from the clone:

```javascript
pristineDOM.querySelectorAll('.darkreader, [class*="darkreader"]').forEach(el => el.remove());
pristineDOM.querySelectorAll('style[class*="extension"], script[class*="extension"]').forEach(el => el.remove());
```

The first selector removes any element with the class `darkreader` or any class containing the substring `darkreader` (Dark Reader injects `<style class="darkreader">` elements). The second selector removes `<style>` and `<script>` elements whose class attribute contains `extension` (a common pattern for other browser extensions that inject content scripts).

These removals operate on the clone only — the live DOM is unaffected.

**Step 3 — Serialization**: A temporary `<div>` is created, the cloned `<html>` element is appended to it (to ensure proper serialization), then `window.PRISTINE_HTML = '<!DOCTYPE html>\n' + pristineDOM.outerHTML`. The `<!DOCTYPE html>` declaration is prepended manually because `outerHTML` does not include it.

This pristine copy is the loader HTML itself (the compressed version), ensuring that downloading the app produces a byte-for-byte identical copy of the original file.

### 24.2.1 Document Clearing and Replacement

After saving `PRISTINE_HTML`, the loader replaces the entire page with the decompressed application HTML:

```javascript
while (document.head.firstChild) {
    document.head.removeChild(document.head.firstChild);
}
while (document.body.firstChild) {
    document.body.removeChild(document.body.firstChild);
}
document.open();
document.write(decompressed);
document.close();
```

Both manual child-removal loops AND `document.open()` are used. The manual clearing removes all existing DOM nodes (the loader spinner, pako script, decompression script). Then `document.open()` implicitly clears the document and opens a new write stream, `document.write()` writes the decompressed HTML, and `document.close()` finalizes parsing. The double clearing (manual + `document.open()`) ensures clean replacement across different browser engines — some browsers do not fully clear existing content on `document.open()` alone.

### 24.2.2 Error Fallback UI

If decompression fails (the `try` block catches any error), the loader replaces the spinner area with a styled error display:

```html
<div class="error">
    <h2>Error Loading Application</h2>
    <p>Failed to decompress the application. This may be due to:</p>
    <ul>
        <li>Browser compatibility issue</li>
        <li>Corrupted file download</li>
        <li>Insufficient memory</li>
    </ul>
    <p>Please try:</p>
    <ul>
        <li>Refreshing the page</li>
        <li>Using a different browser (Chrome, Firefox, Edge recommended)</li>
        <li>Re-downloading the file</li>
    </ul>
    <pre>{error.message}</pre>
</div>
```

The `.error` class is defined in the loader's `<style>` block: semi-transparent white background (`rgba(255,255,255,0.1)`), red-tinted border (`2px solid rgba(255,100,100,0.5)`), rounded corners, left-aligned text. The `<h2>` is light pink (`#ffcccc`). The `<pre>` shows the actual error message on a dark background (`rgba(0,0,0,0.3)`) with horizontal scroll for long messages. The error is also logged to `console.error`.

This error UI is rendered inside the loader's existing gradient background, so it appears as a styled card on the purple gradient — consistent with the app's visual identity even in failure.

### 24.3 Compression

The full application HTML (typically ~4.2 MB) is compressed with `zlib.compress(level=9)` in Python, achieving ~40% reduction. After base64 encoding, the final file is ~2.7 MB.

---

## 25. Self-Download Feature

In the About modal, "The ultimate inception: download this app itself" section:

1. Browser path: Creates a Blob from `window.PRISTINE_HTML` (the loader HTML), creates an object URL, triggers download via a temporary `<a>` element.
2. Android path: Base64-encodes `window.PRISTINE_HTML` and calls `AndroidFileHandler.saveFile()`.

The downloaded file is the self-extracting loader, not the decompressed HTML. It is functionally identical to the original.

---

## 26. Dark Mode

The template contains five `@media (prefers-color-scheme: dark)` blocks (~100 lines total). CSS custom properties are NOT used — each dark mode override is a direct selector with explicit color values.

### 26.1 CSS Dark Mode Overrides

The main dark mode block (lines 1198–1483 in template.html) overrides these component groups:

| Component | What changes |
|---|---|
| `body` | Gradient background (muted purple `#3d4b7a` → `#4a2f5e`) |
| `.container` | Background `#1e1e1e`, text `#e0e0e0`, stronger shadow |
| `h1`, `.subtitle` | Lighter text colors |
| `.upload-area` | Dark background `#2a2a2a`, dark border, dark hover/dragover/file-error states |
| `label[for="pdfFile"]` | Purple button on dark background |
| `.option-group`, `.option-label`, `.radio-option label` | Dark backgrounds, light text |
| `.page-range-input`, `.dpi-value input` | Dark input fields with light text |
| `.dpi-slider`, `.dpi-dimensions`, `.input-hint` | Dark slider track, muted hint text |
| `button`, `.action-btn` | Purple background `#5a3d7a`, darker disabled state `#3a3a3a` |
| `#progress` | Dark blue background `#1e3a52`, blue text `#64b5f6` |
| `#progress.cancelled` | Dark neutral `#2a2a2a`, grey text. `.advanced-content` inside gets `#1e1e1e` background |
| `.credits`, `.credits a` | Muted text, light purple links |
| `.language-switch`, `.language-switch label` | Dark background, light text |
| `.modal-content` | Dark background `#1e1e1e`, light text. Headings, paragraphs, lists, `<pre>` blocks all overridden |
| `.modal-close` | Grey text, light on hover |
| `.license-section`, `.source-section` | Dark borders |
| `.source-toggle`, `.source-textarea` | Light links, dark textarea |
| `.help-button`, `.language-selector-button` | Semi-transparent purple on dark |
| `.language-item` | Dark background, purple active state |
| `.github-corner svg` | Fill overridden to `#4a3d5a` (dark purple, less prominent) |
| `.intro-overlay` | Dark gradient matching body |
| `.intro-container` | Dark background `#1e1e1e` |
| `.intro-upload-area`, `.intro-compress-btn` | Dark borders, dark disabled state |
| `.intro-result-content`, `.intro-size-change`, `.intro-save-btn` | Dark green tones |
| `body.mongolian-script` | Solid dark purple `#3d4b7a` (no gradient — vertical writing breaks gradient rendering in some browsers) |

Four additional dark mode blocks elsewhere in the CSS:

| Location | Selector | What changes |
|---|---|---|
| Flat Earth section | `body.flat-earth .container` | Background `rgba(30,30,30,0.92)` (semi-transparent dark instead of semi-transparent white) |
| AI auto-setter | `.ai-autosetter` | Adjusted box-shadow and border color (pink/purple glow on dark) |
| Input hint box | `.input-hint-box` | Background `#3a3520`, text `#e0c878`, border `#5a4a20` (dark amber instead of light yellow) |
| AI refresh | `.ai-refresh`, `.ai-refresh:hover`, `.ai-refresh-icon` | Dark background `#2a2a2a`, grey icon colors |

### 26.2 Android Theme Styles

The Android app uses four theme style variants to control how the WebView reports `prefers-color-scheme`:

| Style file | Parent theme | Purpose | Extra attributes |
|---|---|---|---|
| `values/styles.xml` | `Theme.DeviceDefault.Light.NoActionBar` | Light mode (default) | `statusBarColor=#000000`, `windowLightStatusBar=false` |
| `values-night/styles.xml` | `Theme.DeviceDefault.NoActionBar` | Dark mode | `statusBarColor=#000000`, `windowLightStatusBar=false` |
| `values-v35/styles.xml` | `Theme.DeviceDefault.Light.NoActionBar` | API 35 light mode | `windowOptOutEdgeToEdgeEnforcement=true` |
| `values-night-v35/styles.xml` | `Theme.DeviceDefault.NoActionBar` | API 35 dark mode | `windowOptOutEdgeToEdgeEnforcement=true` |

The `.Light` parent theme variant causes the WebView to report `prefers-color-scheme: light`; the non-Light variant reports `dark`. The CSS dark mode overrides then apply accordingly.

**Attribute differences between variants**: The non-v35 variants (pre-API 35) include `android:statusBarColor=#000000` (black status bar) and `android:windowLightStatusBar=false` (light-colored status bar icons on the dark bar). The v35 variants do NOT include these attributes — instead they use `android:windowOptOutEdgeToEdgeEnforcement=true` to disable Android 15's mandatory edge-to-edge display. The status bar attributes are omitted from v35 because edge-to-edge enforcement changes how status bar colors work, and the default behavior is acceptable on API 35+.

---

## 27. Accessibility

### 27.1 Semantic Structure

| Element | Attribute | Value | Purpose |
|---|---|---|---|
| Upload area | `role` | `"group"` | Groups the file input and label |
| Upload area | `aria-labelledby` | `"uploadAreaLabel"` | Labels the group with the "Choose PDF File" label |
| Options container | `role` | `"group"` | Groups all form options |
| Options container | `aria-label` | `"Compression options"` | Screen reader name for the options group |
| Conversion mode group | `role` | `"radiogroup"` | Groups the dither radio buttons |
| Conversion mode group | `aria-labelledby` | `"conversionModeLabel"` | Labels with "Conversion Mode:" text |
| Page size group | `role` | `"radiogroup"` | Groups the page size radios |
| Page size group | `aria-labelledby` | `"pageSizeLabel"` | Labels with "Page Size:" text |
| DPI group | `role` | `"radiogroup"` | Groups the DPI mode radios |
| DPI group | `aria-labelledby` | `"outputDpiLabel"` | Labels with "Output DPI:" text |
| Filename display | `aria-live` | `"polite"` | Announces filename changes to screen readers |
| Compress button | `role` | `"button"` | Identifies the div as a button |
| Compress button | `tabindex` | `"0"` | Makes it keyboard-focusable |
| Compress button | `aria-disabled` | `"true"` (initially) | Indicates disabled state (updated by JS) |
| Progress area | `role` | `"status"` | Identifies as a status display |
| Progress area | `aria-live` | `"polite"` | Announces progress updates |
| Page range input | `aria-label` | `"Page range"` | Labels the text input |
| Page range input | `aria-describedby` | `"pageRangeHint"` | Links to hint text below |
| DPI slider | `aria-label` | `"DPI"` | Labels the range input |
| All modals | `role` | `"dialog"` | Identifies as modal dialog |
| All modals | `aria-modal` | `"true"` | Indicates modal behavior |
| License/About/Privacy modals | `aria-labelledby` | `"{id}ModalTitle"` | Labels with the modal's `<h2>` heading |
| Language modal | `aria-label` | `"Select Language"` | Direct label (no `<h2>` heading) |
| Privacy icon container | `aria-hidden` | `"true"` | Hides decorative SVG from screen readers |
| Close buttons | `aria-label` | `"Close"` | Labels the `×` button |
| Intro overlay | `aria-hidden` | `"true"` | Hides animation from screen readers |
| Language selector SVG | `aria-hidden` | `"true"` | Hides decorative icon; button has `aria-label` |
| GitHub corner SVG | `aria-hidden` | `"true"` | Hides decorative icon; link has `aria-label` |
| GitHub corner link | `aria-label` | `"View source on GitHub"` | Screen reader name for the link |

### 27.2 Keyboard Support

- Compress button (`div[role="button"]`): handles Enter and Space keydown events (triggers click).
- `@media (prefers-reduced-motion: reduce)` disables CSS animations and transitions.

---

## 28. Privacy

- No network requests. The Android manifest declares no internet permission.
- No analytics, tracking, cookies, or crash reporting.
- No data leaves the device.
- All processing happens in the browser/WebView.
- Privacy policy effective date: April 2, 2026.
- The privacy policy is embedded in both the About modal and a dedicated Privacy modal.
- The privacy policy SVG icon shows a cloud with wireless signal crossed out in red, overlaying a globe.

---

## 29. Third-Party Components and Licensing

| Component | License | Usage |
|---|---|---|
| PDF.js v2.16.105 (legacy) | Apache 2.0 | PDF rendering in browser |
| pako | MIT | zlib compression/decompression |
| G4Enc | Apache 2.0 | CCITT Group 4 encoder (ported C→JS) |
| jbig2enc | Apache 2.0 | JBIG2 encoder (compiled to WASM) |
| Leptonica v1.84.1 | BSD 2-Clause | Image processing (linked in jbig2enc WASM) |
| LibTIFF | LibTIFF License (BSD-style) | TIFFBitRevTable (in Python CLI tools only) |
| Noto Sans Mongolian | SIL OFL 1.1 | Traditional Mongolian font (302 KB OTF, ~403 KB as base64) |
| img2pdf | LGPL v3+ | Studied for concepts; NO code copied |

The legacy (non-module) PDF.js build is used because the application runs in a non-module `<script>` context. The modern `.mjs` builds are present in the source tree but not used in the build.

All source code for the application itself is under Apache License 2.0. The source code tarball embedded in the HTML file satisfies the Apache 2.0 requirement for source distribution.

### 29.1 img2pdf Clean-Room Rationale

img2pdf (LGPL v3+) was studied to understand CCITT embedding concepts (FillOrder handling, BlackIs1 parameter, general PDF structure for bilevel images). No source code was copied. All implementations are original, based on public domain specifications (TIFF 6.0, PDF 1.4). LGPL only applies to derivative works that copy or link to LGPL code; studying concepts and writing original code is a recognized clean-room practice that does not trigger LGPL obligations. The project is therefore legally Apache 2.0 licensed.

Full license texts are in `LICENSES.md`.

---

## 30. Python CLI Tools

These are standalone command-line equivalents of the web app's functionality. They are NOT used by the web app or the build system (except that build.py generates HTML and build-apk.sh generates the Android project).

### 30.1 pdf_compress.py

Compresses all streams in a PDF with FlateDecode. Cascades on top of existing filters. Similar algorithm to `pdfcompress.js` (section 13) but with some differences noted below. No external dependencies — uses only Python stdlib (`sys`, `zlib`, `re`). Uses `zlib.compress(data, level=9)`.

Usage: `python pdf_compress.py input.pdf output.pdf`

Skips XMP Metadata streams: objects where `/Type` is `Metadata` or `/Subtype` is `XML` are kept uncompressed, matching the JavaScript version (`pdfcompress.js`, section 13.3 step 4). This is required for PDF/A-1B compliance.

#### 30.1.1 Algorithm

The algorithm is structurally similar to `pdfcompress.js` (section 13.3) with these implementation differences:

**Header detection**: Finds the first `\n` (0x0A) after byte offset 20 (the JS version uses offset 10). Everything before that newline is the PDF header.

**Object parsing** (`find_objects`): Scans bytes before the xref table with regex `rb'(\d+) 0 obj\s*'`, then finds `endobj` via `re.search(rb'endobj', ...)` from the match position. Returns list of `{num, start, end, data}` dicts.

**Stream extraction** (`parse_stream_object`): Finds stream boundaries with regex `rb'stream\s*\n'` and `rb'\s*endstream'`. Returns the dictionary bytes (before `stream`), the stream data bytes (between boundaries), and trailing bytes (after `endstream`). Returns `(None, None, None)` for non-stream objects.

**Dictionary parsing** (`parse_dict`): Decodes dictionary bytes as `latin-1` and extracts four fields via regex:
- `/Length`: regex `r'/Length\s+(\d+)'` → integer
- `/Filter`: regex `r'/Filter\s+(/\w+|\[[^\]]+\])'` → filter name or array string
- `/Type`: regex `r'/Type\s+/(\w+)'` → type name (e.g., `Metadata`)
- `/Subtype`: regex `r'/Subtype\s+/(\w+)'` → subtype name (e.g., `XML`)

**XMP Metadata skip**: Objects where `type == 'Metadata'` or `subtype == 'XML'` are kept uncompressed (same logic as `pdfcompress.js`, section 13.3 step 4). Required for PDF/A-1B compliance.

**Compression**: All other streams are compressed with `zlib.compress(stream_data, level=9)`.

**Dictionary update** (`update_dict_with_compression`): Decodes as `latin-1`, applies regex replacements, re-encodes as `latin-1`:
- Updates `/Length` to the compressed size.
- If no existing filter: inserts `/Filter /FlateDecode` before `/Length` (regex: `r'(/Length)'` → `r'/Filter /FlateDecode \1'`).
- If existing single filter: replaces `/Filter /X` with `/Filter [ /FlateDecode /X ]`. If `/DecodeParms <<...>>` is present, replaces with `/DecodeParms [ null <<...>> ]`.

The `cascade_filter` parameter is always passed as `True` — there is no code path that adds FlateDecode without cascading.

**PDF rebuild**: Incremental byte concatenation (not the collect-and-concat strategy used by pdfcompress.js):
1. Starts with the original header.
2. For each object: emits `{i} 0 obj\n` + object data + `\nendobj\n`. Objects are renumbered sequentially starting at 1. Byte offsets are recorded for the xref table.
3. Writes xref table with new offsets.
4. Copies the trailer dictionary from the original PDF via regex `rb'trailer\s*\n(.*?)startxref'` (with `re.DOTALL`). Appends `startxref\n{offset}\n%%EOF\n`.

**Statistics output**: Prints per-object compression details (original size → compressed size, whether cascaded or new FlateDecode), then a summary: object counts by category, original size, compressed size, and reduction percentage.

#### 30.1.2 Known Limitations

- **Single-filter cascading only**: The filter replacement regex `r'/Filter\s+/\w+'` matches only a single filter name. Existing filter arrays are not handled. Same limitation as pdfcompress.js (section 13.7).
- **Shallow DecodeParms matching**: The regex `r'/DecodeParms\s+(<<[^>]+>>)'` does not handle nested dictionaries. Same limitation as pdfcompress.js.
- **Incremental concatenation**: The PDF is rebuilt by repeated `bytes +=` concatenation, which is O(n²) for large files. The JS version uses a collect-and-concat strategy (section 13.3 step 5) that is O(n). For the small PDFs this tool is designed for (output of tiff2pdf_img2pdf.py and jbig2pdf.py), this is not a practical concern.
- **Header offset difference**: Uses byte offset 20 for header end detection (vs 10 in pdfcompress.js). Both values are safe — valid PDF headers are well within either range.

### 30.2 tiff2pdf_img2pdf.py

Converts CCITT Group 4 compressed TIFF files to PDF/A-1B. Embeds the raw CCITT stream data directly in the PDF without re-encoding. No external dependencies — uses only Python stdlib (`struct`, `sys`, `os`, `hashlib`, `datetime`, `time`). Contains `TIFFBitRevTable` from LibTIFF (BSD-style license) for FillOrder=2 bit reversal.

Usage: `python tiff2pdf_img2pdf.py input1.tiff [input2.tiff ...] output.pdf`

The CLI accepts multiple TIFF input files. Each file may be multi-page (TIFF IFD chain). All pages from all input files are merged into a single output PDF. The last argument is always the output filename.

#### 30.2.1 TIFF Parsing

**`read_tiff_file(tiff_path)`** — Reads the TIFF header to determine byte order (`II` = little-endian, `MM` = big-endian), validates the magic number (42), and follows the IFD chain (each IFD contains a pointer to the next, 0 = end) by calling `read_tiff_ifd()` for each page.

**`read_tiff_ifd(f, offset, endian)`** — Reads one IFD (Image File Directory) and extracts image metadata. Parses each 12-byte IFD entry (tag, field type, count, value/offset).

**Supported field types**: Only type 3 (SHORT, 16-bit) and type 4 (LONG, 32-bit) are processed. All other types (BYTE, ASCII, RATIONAL, etc.) are skipped. For SHORT arrays: if `count * 2 <= 4`, values are read inline from the IFD entry; otherwise, a pointer is followed to read from the data area. For LONG arrays, the pointer path is always used for count > 1.

**Extracted TIFF tags**:

| Tag | Name | Purpose |
|---|---|---|
| 256 | ImageWidth | Pixel width |
| 257 | ImageLength | Pixel height |
| 259 | Compression | Must be 4 (CCITT Group 4) — other values cause the page to be skipped |
| 262 | PhotometricInterpretation | 0 = WhiteIsZero (inverted), 1 = BlackIsZero (normal) |
| 266 | FillOrder | 1 = MSB2LSB (default), 2 = LSB2MSB (needs bit reversal) |
| 273 | StripOffsets | Byte offsets to each strip of image data |
| 279 | StripByteCounts | Byte counts for each strip |

**Dimension validation**: Pages with `width <= 0`, `height <= 0`, `width > 20000`, or `height > 20000` are skipped with a warning. This 20,000-pixel limit is a safety guard.

**Data extraction**: Reads raw CCITT data by iterating `zip(strip_offsets, strip_bytes)` and seeking to each strip. Validates that `len(chunk) == size` for each strip — incomplete reads cause the page to be skipped. Data is concatenated from all strips.

**FillOrder handling**: If `fillorder == 2` (LSB2MSB), every byte of the CCITT data is reversed using `TIFFBitRevTable[byte]` — the 256-entry bit-reversal lookup table from LibTIFF. This converts LSB-first data to the MSB-first order expected by PDF CCITT decoders.

**BlackIs1 determination**: Tracked via `inverted = (photo == 0)`. When the TIFF's photometric interpretation is WhiteIsZero (0), the PDF `/DecodeParms` uses `/BlackIs1 false`; when BlackIsZero (1), it uses `/BlackIs1 true`. This ensures consistent rendering regardless of the TIFF's photometric convention.

**Known limitations**:
- Only strip-based TIFFs are supported (`StripOffsets` / `StripByteCounts`). Tiled TIFFs (using `TileOffsets` / `TileByteCounts`) are silently unsupported — the parser simply won't find strip tags and will skip the page.
- Only CCITT Group 4 (compression=4) is supported. Other compression methods cause the page to be skipped.

#### 30.2.2 PDF Generation

`create_pdf(pages, output_path)` generates a PDF/A-1B file. The structure is equivalent to pdfgen.js (section 12.1) with these differences:

**Page sizing**: Fixed A4 portrait (`595 × 842` pt). Unlike pdfgen.js, the Python tool does not support page size selection — A4 is always used. Scaling and centering use the same aspect-ratio-preserving algorithm as pdfgen.js (section 12.2). Content stream CTM values use `.4f` precision.

**BlackIs1 parameter**: Dynamic per page based on the TIFF's photometric interpretation (see section 30.2.1). The JS version always uses `/BlackIs1 false` because the polarity inversion is done before encoding.

**`/Decode [0 1]`**: Present in the image XObject, same as pdfgen.js.

**CalGray colorspace**: `[/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]` — identical to pdfgen.js (section 12.1.2).

**PDF/A-1B structure**: XMP Metadata (`pdfaid:part=1`, `conformance=B`), OutputIntent (`GTS_PDFA1`, `Gray Gamma 2.2`), MarkInfo (`/Marked true`), ViewerPreferences (`/DisplayDocTitle true`) — all identical to pdfgen.js (section 12.1.3). The XMP `CreatorTool` and `Producer` are both set to `"tiff2pdf_img2pdf.py (PDF to CCITT Converter)"` (not configurable, unlike pdfgen.js which has include/exclude options).

**Object numbering**: `pages_obj_num = obj_num + (len(pages) * 3)` — same formula as pdfgen.js. Each page produces 3 objects (image, content, page), followed by Pages, Metadata, OutputIntent, Catalog.

**PDF header**: `%PDF-1.4\n%\xe2\xe3\xcf\xd3\n` — identical binary marker bytes as pdfgen.js.

**PDF assembly**: Incremental bytes concatenation (`pdf += ...`), same as pdf_compress.py. Not the collect-and-concat strategy used by pdfgen.js.

**File ID generation**: Uses `hashlib.md5()` — a real MD5 hash (unlike pdfgen.js which uses a `simpleHash` function named `md5` that is not actually MD5):

```python
id_source = f"{output_path}{time.time()}{len(pages)}".encode()
file_id = hashlib.md5(id_source).hexdigest().upper()
```

The 32-character hex output is used directly for both entries in the PDF `/ID` array.

### 30.3 jbig2pdf.py

Converts jbig2enc output (`.sym` + `.0000`-`.NNNN` files) to PDF/A-1B with JBIG2Decode filter. No external dependencies — uses only Python stdlib (`struct`, `sys`, `os`, `glob`, `hashlib`, `datetime`, `time`).

Usage: `python jbig2pdf.py <jbig2_prefix> <output.pdf>`
Example: `python jbig2pdf.py /tmp/output /tmp/result.pdf` (reads `/tmp/output.sym`, `/tmp/output.0000`, etc.)

#### 30.3.1 Input File Discovery

`create_jbig2_pdf(jbig2_prefix, output_path)` discovers input files by:

1. **Page segments**: `glob.glob(f"{jbig2_prefix}.[0-9][0-9][0-9][0-9]")`, sorted. Matches `output.0000`, `output.0001`, etc. Exits with error if none found.
2. **Global symbol dictionary**: Reads `{prefix}.sym` if it exists. Stored as raw bytes for embedding as a PDF stream object.
3. **Page dimensions from PBM files**: The PBM filename prefix is inferred from the jbig2 prefix basename: if `'dither'` appears in the basename, PBM files are `dither-page-NNNN.pbm`; otherwise `page-NNNN.pbm`. PBM files are looked for in the same directory as the prefix.

#### 30.3.2 JBIG2 Segment Parser (dead code)

`read_jbig2_metadata(jbig2_data)` is defined in the file but **never called** — neither by `create_jbig2_pdf()` nor by the CLI entry point. The tool obtains page dimensions exclusively from PBM files (section 30.3.3), falling back to hardcoded A4 dimensions if PBM files are missing. The JBIG2 segment parser is not used as a secondary fallback.

The function uses the same algorithm as the JavaScript version in jbig2pdf.js (section 11.8.1) and could theoretically be wired in as a fallback for cases where PBM files are unavailable but JBIG2 data contains page information segments. This is a potential future enhancement, not a current feature.

#### 30.3.3 PBM Dimension Reader

`read_pbm_dimensions(pbm_path)` reads the header of a binary PBM (P4 format) file:

1. Reads the magic line — must be `P4`.
2. Reads subsequent lines, skipping comment lines starting with `#`.
3. Parses the first non-comment line as `width height` (space-separated).

Returns `(width, height)` tuple, or `(None, None)` on any error (bare `except: pass`).

**A4 fallback**: If PBM files are missing or unreadable, dimensions default to A4 at 310 DPI: `width = int(210 / 25.4 * 310)` = 2551 pixels, `height = int(297 / 25.4 * 310)` = 3622 pixels.

#### 30.3.4 PDF Generation

The PDF/A-1B structure is adapted from tiff2pdf_img2pdf.py (section 30.2.2) with JBIG2-specific changes:

**Object numbering**: Unlike tiff2pdf_img2pdf.py (which pre-calculates `pages_obj_num`), jbig2pdf.py uses a sequential counter and references the Pages object's `/Parent` via `f"/Parent {obj_num} 0 R"` inside the page object loop. This works because `obj_num` at that point equals the Pages object number — each page produces 3 objects (image, content, page), the global dictionary (if present) is object 1, and the Pages object immediately follows the last page object. **This is a fragile coincidence**: if the object creation order were changed, the Parent references would break silently. The JS version (section 11.8.2) avoids this by pre-calculating `pagesObjNum`.

**Global symbol dictionary**: If `global_data` is present, it becomes the first object (a raw stream with just `/Length`, no filter). Its object number is referenced by every page's image XObject via `/DecodeParms << /JBIG2Globals {global_obj_num} 0 R >>`. Without global data, `/DecodeParms << >>` is used.

**Image XObject**: `/Filter /JBIG2Decode`, CalGray colorspace, `/Decode [0 1]`, `/BitsPerComponent 1`. Same as jbig2pdf.js (section 11.8.2).

**Content stream, page sizing, centering**: Fixed A4 (595×842 pt), `.4f` precision — same as tiff2pdf_img2pdf.py.

**XMP Metadata**: `CreatorTool` and `Producer` both set to `"jbig2pdf.py"`.

**File ID**: `hashlib.md5(f"{output_path}{time.time()}{len(pages)}")` — same pattern as tiff2pdf_img2pdf.py (section 30.2.2).

**PDF assembly**: Incremental bytes concatenation, same as tiff2pdf_img2pdf.py.

---

## 31. Shell Example Scripts

### 31.1 ccitt_g4_pdf_compression_example.sh

Demonstrates the full CCITT G4 compression workflow using CLI tools:
1. `gm convert` (GraphicsMagick): PDF → bilevel TIFF at specified DPI. Applies `-despeckle`, grayscale conversion, normalize, level 10%/90%, bilevel conversion. Non-dithered variant uses `+dither` flag (GraphicsMagick syntax: `+dither` disables dithering). Dithered variant omits the flag.
2. `tiff2pdf_img2pdf.py`: TIFF → PDF/A-1B.
3. `pdf_compress.py`: FlateDecode compression of all PDF streams.

### 31.2 jbig2_pdf_compression_example.sh

Demonstrates JBIG2 compression:
1. `gm convert`: PDF pages → individual PBM files at 310 DPI with same preprocessing as CCITT example.
2. Normalize PBM files to A4 portrait dimensions (2562×3625 at 310 DPI) using `-resize` to fit within bounds, then `-extent` with `-gravity center` to pad to exact size with white background.
3. `jbig2enc -s -p -a -d -t 0.97`: Encode PBMs to JBIG2. Flags: `-s` symbol coding, `-p` PDF-compatible segments, `-a` automatic thresholding, `-d` TPGD duplicate line removal, `-t 0.97` matching threshold.
4. `jbig2pdf.py <prefix> <output.pdf>`: JBIG2 → PDF/A-1B.

---

## 32. WASM Build System

File: `wasm/build-jbig2-wasm.sh`

Requirements: Emscripten SDK (emsdk)

Steps:
1. Downloads and compiles Leptonica v1.84.1 with Emscripten (`emconfigure`, `emmake`). All optional image format libraries are disabled (`-DENABLE_GIF=OFF -DENABLE_JPEG=OFF -DENABLE_PNG=OFF -DENABLE_TIFF=OFF -DENABLE_WEBP=OFF -DENABLE_OPENJPEG=OFF`).
2. Clones jbig2enc at commit 4cadbfe.
3. Applies `jbig2enc-emscripten.patch` (two patches in `jbig2.cc`: replaces POSIX `open()/write()/close()` with `fopen()/fwrite()/fclose()` for both the global symbol dictionary write and the per-page segment writes).
4. Compiles jbig2enc with Emscripten, linking against compiled Leptonica.
5. Key Emscripten linker flags: `-s FORCE_FILESYSTEM=1 -s ALLOW_MEMORY_GROWTH=1 -s EXPORTED_RUNTIME_METHODS=['FS','callMain'] -s MODULARIZE=0 -s EXPORT_NAME='Module' -s INVOKE_RUN=0 -sSTACK_SIZE=32MB`. The `MODULARIZE=0` and `EXPORT_NAME='Module'` flags are critical for the re-initialization pattern in section 11.2 (the loader creates a global `var Module` that can be replaced by `new Function()`).
6. Outputs `jbig2.wasm` and `jbig2.js`.

---

## 33. i18n Validation Tools

### 33.1 i18n-validate.js (Structural Validator)

File: `i18n-tools/i18n-validate.js` (327 lines). Requires Node.js.

Usage: `node i18n-tools/i18n-validate.js` (from `webapp_build/`) or `cd i18n-tools && node i18n-validate.js`.

The authoritative structural validator. Uses `eval()` to parse the actual JavaScript object literals from `i18n.js` and `i18n-languages.js`, giving it access to the real parsed objects (not regex approximations).

**Directory auto-detection**: Checks if `process.cwd()` basename is `'i18n-tools'` — if so, files are at `../i18n.js`; otherwise at `./i18n.js`.

**Extraction algorithm** (`extractTranslationsFromFile`):
1. Reads the file, finds `const TRANSLATIONS = {` or `const ADDITIONAL_TRANSLATIONS = {` via regex.
2. From the opening `{`, counts braces to find the matching `}` (brace-counting parser, not regex for the object body).
3. Wraps the extracted object literal in parentheses and calls `eval()` to parse it. This handles all valid JavaScript syntax (trailing commas, template strings, etc.) that regex-based parsers would miss.

**Validation checks** (run in order):

| Check | Function | Counts as error? |
|---|---|---|
| Duplicate keys | `checkDuplicateKeysFromSource` | Yes — scans the raw source text of each file with a character-level state machine that tracks string state (both quote types, with escape handling), line comments, and brace depth. Collects key names at depth 2 (translation keys within each language block) and reports any that appear more than once per language. Operates on the source text before `eval()`, so it detects duplicates that JavaScript would silently merge. Handles bare identifier keys (`title:`) and quoted keys (`"zh-Hans":`, `'sr-Cyrl':`). |
| Missing required fields | `checkMissingFields` | Yes — checks against `REQUIRED_FIELDS` list |
| Deprecated fields | `checkDeprecatedFields` | Yes — checks against `DEPRECATED_FIELDS` list |
| Unexpected extra fields | `checkExtraFields` | **No** — printed as warnings (⚠️) but NOT added to `totalIssues` |
| Required placeholders | inline loop | Yes — checks `PLACEHOLDER_REQUIREMENTS` map |
| Empty/non-string values | `checkEmptyValues` | Yes — flags empty strings (`value.trim() === ''`) and non-string types |

**`DEPRECATED_FIELDS`**: `['outputFormat', 'dpiDimensions', 'highFilesizeWarning', 'highComputeWarning']` — fields that were renamed or removed during development. Their presence in a translation is an error.

**`PLACEHOLDER_REQUIREMENTS`**: A map of field names to required placeholder strings:
- `ramWarningHigh`, `ramWarningCritical` → must contain `{ram}`
- `jbig2DisabledMpix` → must contain `{mpix}`
- `jbig2DisabledPages`, `fileInfoPageCount` → must contain `{pages}`
- `fileInfoFileSize` → must contain `{size}`

**Exit codes**: `process.exit(1)` if `totalIssues > 0`, `process.exit(0)` otherwise. Extra fields (warnings) do NOT cause failure.

### 33.2 i18n-validate-legacy.py (Semantic Validator)

File: `i18n-tools/i18n-validate-legacy.py` (~400 lines). Requires Python 3. No external dependencies.

Usage: `python3 i18n-tools/i18n-validate-legacy.py` (from `webapp_build/`) or `cd i18n-tools && python3 i18n-validate-legacy.py`.

Complements the JS validator with semantic checks that require cross-language comparison. Uses regex-based extraction (less accurate than `eval()` but sufficient for semantic analysis).

**Directory auto-detection**: Same pattern as the JS validator — checks `os.path.basename(cwd)`.

**Reference languages**: `['en', 'de', 'cs', 'sk', 'pl', 'ru']` — assumed correct; semantic checks are only run against non-reference languages.

**Extraction algorithm** (`extract_translations`):
1. Finds language blocks with regex `r'^\s*["\']?([a-z]{2}(?:-[A-Za-z]+)?)["\']?\s*:\s*\{'` (multiline).
2. From each match, counts braces to find the matching `}`.
3. Extracts field values with two regexes: `r'(\w+):\s*"([^"]*)"'` (double-quoted, primary) and `r"(\w+):\s*'([^']*)'` (single-quoted, fallback — does not override double-quoted matches).
4. **Known limitation**: These regexes cannot handle escaped quotes (`\"` inside a string) or multi-line string values. This is acceptable because i18n translation strings are always single-line and do not contain escaped quotes.

**Validation checks**:

1. **Missing required fields** (`check_missing_fields`) — same `REQUIRED_FIELDS` list as the JS validator.
2. **Deprecated fields** (`check_deprecated_fields`) — same `DEPRECATED_FIELDS` list.
3. **Preserved technical terms** (`check_preserved_terms`) — checks that terms appearing in reference translations also appear verbatim in non-reference translations. Terms: `PDF`, `DPI`, `G4`, `CCITT`, `A4`, `Letter`, `Legal`, `PDF.js`, `pako`, `G4Enc`, `Apache 2.0`. Allows case variations (`term.lower()`, `term.upper()`).
4. **Landscape/orientation** (`check_landscape_orientation`) — detects translations where "landscape" may have been translated as "scenery/vista" rather than "page orientation." Uses a `vista_terms` set containing known problematic translations: `krajobraz`, `pejzaž`, `пейзаж`, `peizazh`, `peisaj`, `ainava`, `landscape`, `paisagem`, `paisaje`, `paesaggio`. If a vista term appears in `pageSizeA4Landscape` alongside "A4", checks whether orientation indicators (`vertical`, `horizontal`, `patayo`, `pahiga`, `вертикально`, `горизонтально`, `uspravno`, `položeno`) appear in portrait/landscape fields. Reports a warning if not.
5. **Script consistency** (`check_script_consistency`) — verifies that each translation uses the expected writing system. Maps 36 language codes to expected scripts:

   | Script | Languages |
   |---|---|
   | Arabic | ar, ur |
   | Cyrillic | ru, uk, bg, sr-Cyrl, be, mk, mn, kk |
   | Devanagari | hi, mr |
   | Bengali | bn |
   | Tamil | ta |
   | Telugu | te |
   | Gujarati | gu |
   | Gurmukhi | pa |
   | Kannada | kn |
   | Malayalam | ml |
   | Hebrew | he, yi |
   | Thai | th |
   | Georgian | ka |
   | Armenian | hy |
   | Ethiopic | am |
   | Tibetan | bo |
   | Myanmar | my |
   | Khmer | km |
   | Lao | lo |
   | Han | zh-Hans, zh-Hant |
   | Japanese | ja |
   | Hangul | ko |
   | Sinhala | si |
   | Latin | sr-Latn, uz, az |

   The `detect_script(text)` function counts characters in 24 Unicode ranges and returns the predominant script. Latin is always accepted as a secondary script (technical terms like "PDF" are Latin even in non-Latin languages). Only the `title` field is checked.

**Exit codes**: `sys.exit(0)` on pass, `sys.exit(1)` on failure.

### 33.3 validate-all.sh

Runs both validators sequentially with `set -e`. If the first validator (JS) fails, the script exits immediately with code 1 — the second validator (Python) does not run. This is intentional: all validations must pass, so there is no point continuing after a failure. The validator's own output identifies the specific issues.

When both validators pass, the script reaches the summary block which captures exit codes via `JS_EXIT=$?` / `PY_EXIT=$?` and prints a combined pass/fail report. The summary block and exit-code-capture logic are only reachable on the success path (both validators exit 0), which is the only case where `$?` capture works correctly under `set -e`.

### 33.4 normalize-locale-codes.py

Build support utility (not a CLI tool). Normalizes BCP 47 locale code casing in `i18n.js`, `i18n-languages.js`, and `build.py`. Uses the same algorithm as the runtime `normalizeBCP47()` function (section 46.1): language lowercase, 4-char script subtags titlecase, 2-char region subtags uppercase. Run manually after adding new locale codes to ensure consistent casing across all files.

---

## 34. Pitfalls, Gotchas, and Non-Obvious Behaviors

### 34.1 G4 Encoder Polarity

The G4 encoder (from G4ENC) treats bit=1 as WHITE. The image processing pipeline treats bit=1 as BLACK. The data must be bitwise-inverted before encoding. Forgetting this produces a negative image.

### 34.2 G4 Encoder Buffer Sizing

The original G4ENC C code was designed for microcontrollers with a 1 KB buffer and 1024-pixel max width. At 1200 DPI on A4, worst case (alternating pixels) produces ~11.8 KB per line. The buffer was increased to 128 KB with a 10x safety margin.

The buffer must NEVER flush mid-line. The original C code flushes only at line boundaries (between `encodeLine()` calls). An early attempt to add mid-line flushing in `insertCode()` caused corruption because the 32-bit register's partial bits, buffer position arithmetic, and byte alignment all assume continuity within a line. The fix is to make the buffer large enough that mid-line flushing is never needed.

If a future change increases MAX_DPI beyond 1200 or supports larger page sizes, recalculate: worst-case bits per line = (width/2) runs × 19 bits/run, divide by 8 for bytes, then add safety margin.

### 34.2a G4 Padding Bits in Non-Byte-Aligned Widths

For widths not divisible by 8 (e.g., A4 at 310 DPI = 2478 pixels = 309.75 bytes), the last byte contains padding bits. The `encodeLine()` function must clamp the final run-end position to `xsize`, not count the padding bits. Without clamping, the run-end position is 2480 instead of 2478. This causes the encoder to select a wrong mode (e.g., pass mode instead of vertical V(0)), which corrupts the reference line, and the error cascades through all subsequent lines — turning compression into expansion.

The fix: `if (x > xsize) x = xsize;` at the end of `encodeLine()`.

The boundary checks inside the color-change loops do not catch this because all-white or all-black lines have no color changes and bypass those checks entirely.

### 34.2b G4 Run-End Format

The G4 encoder uses run-end format (positions where color changes) rather than run-length format. Example: `WWWWBBBWWW` → run-ends `[4, 7, 10]`. The array must start with the position of the first black pixel (or `xsize` if all-white), must end with `xsize` repeated 4 times as a sentinel, and all positions must be ≤ `xsize`.

### 34.2c G4 Debugging Symptoms

| Symptom | Likely Cause |
|---|---|
| Data expansion (>100%) | Wrong encoding mode selection (check a1/b1/b2 logic) or padding bits being counted |
| Visual noise/artifacts | Padding bits, or bit order issue |
| Corruption after N lines | Reference line contamination (curFlips/refFlips swap) |
| Identical corruption across different inputs | Bug in encodeLine(), not buffer management |
| Random corruption | Buffer overflow or bit register corruption |

### 34.3 PDF.js Worker Blob URLs in Android WebView

PDF.js worker is created as a Blob URL from base64-decoded data. Android WebView loaded from `file:///android_asset/` cannot load `blob:null/...` URLs, so PDF.js falls back to a "fake worker" (runs in the main thread). This works correctly but may be slower than a real worker. The `blob:null` errors in logcat are harmless.

### 34.4 JBIG2 Module Re-initialization

The Emscripten loader uses `var Module = ...` which relies on `var` hoisting. On first load, this works in global scope. For re-initialization, `new Function(source)()` is used, which creates a new scope where `var Module` hoists correctly. Without the patch to use `window.Module||{}`, re-init would create a fresh Module ignoring the one on `window`.

### 34.5 CCITT G4 BlackIs1 Parameter

The PDF `/DecodeParms` uses `/BlackIs1 false`. This means: in the CCITT stream, 1-bits represent WHITE pixels. This matches the G4 encoder's convention (after our inversion). Changing this to `true` without also changing the polarity inversion would produce incorrect output.

### 34.6 PDF FlateDecode Cascading on XMP

XMP Metadata streams must NOT be FlateDecode-compressed for PDF/A-1b compliance. The pdfcompress.js skips any object with `/Type /Metadata` or `/Subtype /XML`. Removing this check would break PDF/A-1b validation.

### 34.7 resetAppState() vs _lastKnownState

`resetAppState()` does NOT clear `_lastKnownState`. This is intentional: `_lastKnownState` must survive resets to enable restoration. It is declared outside the `resetAppState()` function scope.

### 34.8 handleFileSelected() Resets resultSettings

`handleFileSelected()` calls `cleanupPreviousResult()` which resets `resultSettings` to defaults. Therefore, in `restoreAppState()`, the Advanced Tricks values (JBIG2, threshold, rotation, producer, timestamp) must be repopulated AFTER `handleFileSelected()` completes (in the `.then()` callback), not before.

### 34.9 autoAdjustDPI Guard

`autoAdjustDPI()` returns early when `restoringState` is true. Without this guard, restoring a custom DPI (e.g., 200) would be immediately overridden to 310 by auto-adjustment.

### 34.10 Browser Form Restoration Detection

Browsers may restore form values from history on navigation. A `setTimeout(100ms)` detects this and calls `resetAppState()`. This timer is ONLY registered when `_lastKnownState` is null (no Android/bfcache restore in progress). Placing it unconditionally caused a race condition where restored values were wiped.

### 34.11 deepCleanMemory Timing

`saveAppState()` must be called BEFORE `deepCleanMemory()` in the compress handler and AI auto-setter. `deepCleanMemory()` destroys the Advanced Tricks DOM elements, making `getCurrentFormState()` return defaults for JBIG2/rotation/metadata fields. If OOM occurs during compression and the WebView restarts, the state saved before `deepCleanMemory()` will be used for restoration.

### 34.12 WebView Kill on Save (Tier 1/2)

When saving on tier 1/2, the WebView is destroyed BEFORE showing the SAF dialog. This means:
- The save button's "saving" class is irrelevant (button is destroyed).
- After save completes, `showSaveResultAnimation()` shows a diskette SVG animation for 4 seconds, then `recreateWebView()` starts a fresh WebView load.
- `recreateWebView()` sets `skipIntroOnReload = true` and calls `setupWebView()` + `loadUrl()`.
- On the new page load, `hasRestoredState()` returns true, and the full state restore path runs.

### 34.13 configChanges Attribute

`android:configChanges="orientation|screenSize|keyboardHidden"` prevents Activity recreation on rotation. This is critical because all state preservation relies on Java instance variables, which would be lost on Activity recreation. The WebView handles orientation changes internally.

### 34.14 Persisted URI Permissions

`ACTION_OPEN_DOCUMENT` URIs support `takePersistableUriPermission()`. However, these permissions accumulate across app sessions. `onCreate()` releases all persisted permissions on every fresh start to prevent stale URI buildup. A new permission is taken each time a file is selected.

### 34.15 Save Animation WebView

The save result animation uses a separate WebView (not the main one) with `setJavaScriptEnabled(false)`. It loads a minimal HTML page with an SVG diskette and CSS animation. After 4 seconds, it is destroyed and the main WebView is recreated.

### 34.16 Memory Probe SharedPreferences

Probe state uses `commit()` (synchronous), not `apply()` (asynchronous). This ensures the state is persisted to disk before the app might be killed. Using `apply()` would risk losing the state if the OS kills the app during the probe.

### 34.17 ZIP Entry GC Decoupling

In `parseZip()`, stored (method 0) entries use `.slice()` instead of direct `subarray()`. `subarray()` creates a view into the original ArrayBuffer, preventing GC of the full ZIP data. `.slice()` creates an independent copy, allowing the parent ArrayBuffer to be freed when nulled (important for tier 1/2 memory freeing in `convertZIP()`).

### 34.18 validateFormMatchesResult

The save button is disabled (grayed out) whenever current form settings differ from the settings used to create the current result. This prevents saving a result that doesn't match what the user sees in the form. Checking is done by comparing all 10 settings fields.

### 34.19 File Re-selection

The file input's `click` handler sets `this.value = ''`, ensuring the `change` event fires even when the same file is re-selected. Without this, selecting the same file again would be a no-op.

### 34.20 JBIG2 Encoder Memory

The JBIG2 encoder writes PBM files directly to the WASM MEMFS. This keeps bilevel data out of JS heap. However, the WASM module's linear memory (`Module.HEAP`) grows and cannot shrink. `initJBIG2Module()` destroys and recreates the entire WASM instance to reclaim this memory.

### 34.21 Mongolian Wheel Scroll

In Mongolian script mode (vertical writing), mouse wheel events on the container are intercepted: `deltaY` is redirected to `scrollLeft` to enable horizontal scrolling with a vertical scroll wheel.

---

## 35. Testing Procedures

### 35.1 Web App Testing

1. Open `pdf-to-g4-compressor.html` in a browser.
2. Select a PDF file containing scanned document pages.
3. Test each dithering mode (no dither, dither, dither-selected with page range).
4. Test each page size and DPI setting.
5. Test JBIG2 mode with different thresholds.
6. Test the AI auto-setter button.
7. Test cancellation during conversion.
8. Test ZIP file input with multiple PDFs.
9. Verify the output PDF opens correctly in a PDF viewer.
10. Test all modals (License, About, Privacy, Language).
11. Test dark mode.
12. Test RTL languages (Arabic, Hebrew).
13. Test Traditional Mongolian script mode.
14. Test the self-download feature.
15. Test the source tarball extraction.

### 35.2 Android Testing

1. Build and install the APK.
2. First launch: verify calibration completes and tier is detected.
3. Select a PDF, compress, save.
4. On tier 1/2 device: verify WebView is killed during save, state is restored after.
5. Force OOM by putting app in background and opening memory-heavy apps. Return and verify state restoration.
6. Test file re-selection after save.
7. Test back button with modals open.
8. Test rotation during compression.
9. Verify external links open in browser.
10. Test dark mode toggle in system settings.

### 35.3 Console Verification

On initialization, the browser console should show:
```
PDF.js worker configured from inline code
PDF Monochrome CCITT G4 Compressor - Initializing...
Detected language: <code>
DOM elements loaded: {pdfFileInput: true, convertBtn: true, ...}
[JBIG2] WASM binary prepared: <N> bytes
[JBIG2] Runtime initialized
PDF Monochrome CCITT G4 Compressor - Ready!
```

During conversion, per-page messages show rendering dimensions, bilevel conversion, G4 stream sizes, and compression ratios.

### 35.4 Output Verification

```bash
# Check CCITT streams in output PDF
pdfimages -list output.pdf
# Expected: Type=image, Filter=CCITTFaxDecode/FlateDecode, Color=gray 1-bit

# Validate PDF/A-1b compliance
verapdf --flavour 1b output.pdf

# Extract CCITT images for inspection
pdfimages -ccitt output.pdf extracted
tiffinfo extracted-000.tif
```

### 35.5 Validation

- Run `validate-all.sh` to check all translations.
- Open output PDFs in multiple viewers (Adobe, Preview, Firefox, Chrome).
- Verify PDF/A-1b compliance using a validator.
- Check that XMP metadata is uncompressed (required by PDF/A-1b).
- Verify CalGray colorspace is used (not DeviceGray).

---

## 36. Android Locale Resource Generation

### 36.1 Purpose

Google Play Console detects supported languages only from Android resource directories (`values-XX/strings.xml`), not from JavaScript inside the WebView's HTML. Without generated locale resources, the Play Store listing would show only the default language.

### 36.2 Implementation

`build-apk.sh` generates a Python script `GENERATE-ANDROID-LOCALES.py` in the `android-build/` directory as a heredoc, makes it executable (`chmod +x`), and runs it immediately. The script's output is suppressed: `python3 GENERATE-ANDROID-LOCALES.py > /dev/null 2>&1`. The exit code is checked — on failure, a warning is printed but the build continues.

#### 36.2.1 Language Extraction

`extract_languages_from_i18n(i18n_dir)` reads both `i18n.js` and `i18n-languages.js` from `../src/webapp_build/` (path relative to `android-build/`). For each file, it applies a verbose regex to extract language codes and their `title` field values:

```python
pattern = r"""
    ^\s+                          # Leading whitespace
    ['\"]?                        # Optional quote around key
    ([a-z]{2,3}(?:-[A-Za-z]+)?)  # Language code (group 1)
    ['\"]?                        # Optional quote
    \s*:\s*\{                     # Colon and opening brace
    .*?                           # Anything (non-greedy)
    title:\s*['"](.*?)['"]        # Title string value (group 2)
"""
```

Flags: `re.MULTILINE | re.DOTALL | re.VERBOSE`. This matches patterns like `en: { title: "PDF Monochrome G4 Compressor", ...` and captures `('en', 'PDF Monochrome G4 Compressor')`. The `.*?` with `re.DOTALL` allows the title field to appear anywhere within the object (it need not be the first field).

Returns a dict mapping language codes to their title strings (used as Android `app_name`).

#### 36.2.2 Calibrating Strings

The script contains a hardcoded `calibrating_strings` dictionary with 73 pre-translated calibration messages. These translations are NOT from the i18n.js files — they are separate because the calibration screen is rendered natively by Java (section 21.3), before the WebView and its JavaScript translations are loaded.

Examples:
- `'en': 'First launch, calibrating…'`
- `'de': 'Erster Start, Kalibrierung…'`
- `'ja': '初回起動、キャリブレーション中…'`
- `'ar': 'أول إطلاق، جارٍ المعايرة…'`
- `'zh-Hans': '首次启动，正在校准…'`

The dictionary covers: en, de, es, fr, it, pt, nl, pl, cs, sk, ru, uk, ar, he, ja, ko, zh-Hans, zh-Hant, tr, hi, bn, th, vi, id, ms, tl, sv, da, nb, nn, fi, el, bg, ro, hu, hr, sr, sr-Latn, sl, et, lv, lt, ka, hy, fa, ur, sw, af, ca, eu, gl, is, mk, bs, sq, mn, az, uz, kk, ky, be, am, ne, si, km, lo, my, ta, te, kn, ml, mr, gu, pa, or, zu, jv.

For languages not in the dictionary, the script falls back to the base language (`js_code.split('-')[0]`), then to English: `calibrating_strings.get(js_code, calibrating_strings.get(js_code.split('-')[0], 'First launch, calibrating…'))`.

#### 36.2.3 Resource Generation

`create_android_resources(languages, res_dir)` iterates all extracted languages and for each:

1. **Skip exclusions**: `mn-Mong` (Android resource system doesn't support this script tag), `*-FE` joke locales, `67` (brainrot).

2. **Map locale code**: `js_to_android_locale()` applies the mapping in section 36.3. Unmapped codes pass through unchanged.

3. **English special case**: If the Android code is `'en'`, the resource goes into the default `values/` directory (NOT `values-en/`). Android treats `values/` as the default locale, and English is the app's default language. Using `values-en/` would create a separate English entry that might conflict with the default.

4. **Create directory and strings.xml**:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <resources>
       <string name="app_name">{title from i18n}</string>
       <string name="calibrating">{calibrating string}</string>
   </resources>
   ```

   The `app_name` is the translated `title` field from i18n (e.g., German: "PDF Monochrom G4 Kompressor"). The `calibrating` string comes from the hardcoded dictionary (section 36.2.2).

### 36.3 Locale Code Mapping (JavaScript → Android)

| JS Code | Android Directory | Notes |
|---|---|---|
| zh-Hans | zh-rCN | Simplified Chinese |
| zh-Hant | zh-rTW | Traditional Chinese |
| sr-Cyrl | sr | Serbian Cyrillic (default) |
| sr-Latn | b+sr+Latn | Serbian Latin (BCP 47 format) |
| he | iw | Android legacy code |
| id | in | Android legacy code |
| yi | ji | Android legacy code |
| fil | tl | Filipino = Tagalog |
| mn-Mong | _(skipped)_ | Android resource system does not support this script tag |

Joke locales (en-FE, cs-FE, sk-FE, 67) are excluded from Android resources.

---

## 37. Android Emulator and Screenshot Automation

`build-apk.sh` generates several automation scripts into `android-build/`:

### 37.1 Emulator Definitions

`setup-emulators.sh` creates 12 AVDs using the system image `system-images;android-34;google_apis;x86_64`. A `create_avd()` helper function handles each AVD: deletes any existing AVD with the same name, creates a new one via `avdmanager create avd`, then appends configuration to `config.ini` (`hw.gpu.enabled=yes`, `hw.gpu.mode=auto`, `hw.ramSize`, `hw.keyboard=yes`).

**Google Play screenshot AVDs** (3, default 2048 MB RAM):

| AVD Name | Device | Display | Purpose |
|---|---|---|---|
| `screenshot_phone` | `pixel_6` | 6.4", 1080×2400, 411 DPI | Phone screenshots (required) |
| `screenshot_tablet_7` | `Nexus 7` | 7", 800×1280, 213 DPI | 7-inch tablet screenshots (required) |
| `screenshot_tablet_10` | `pixel_tablet` | 10.95", 1600×2560, 280 DPI | 10-inch tablet screenshots (required) |

**RAM tier testing AVDs** (9, various RAM sizes):

| AVD Name | Device | RAM | Expected tier |
|---|---|---|---|
| `ram_500mb` | `pixel_3a` | 500 MB | Tier 1 |
| `ram_700mb` | `pixel_3a` | 700 MB | Tier 1 |
| `ram_1000mb` | `pixel_3a` | 1000 MB | Tier 2 |
| `ram_1500mb` | `pixel_3a` | 1500 MB | Tier 2 |
| `ram_2000mb` | `pixel_3a` | 2048 MB | Tier 2/3 boundary |
| `ram_4gb` | `pixel_6` | 4096 MB | Tier 3 |
| `ram_6gb` | `pixel_6` | 6144 MB | Tier 3 |
| `ram_8gb` | `pixel_6` | 8192 MB | Tier 3 |
| `ram_10gb` | `pixel_6` | 10240 MB | Tier 3 |

Low-RAM tiers (≤2048 MB) use `pixel_3a`; high-RAM tiers use `pixel_6`.

### 37.2 Emulator Run Scripts

Each AVD has a corresponding run script generated by `build-apk.sh`:

**Screenshot emulators** (`run-emulator-phone.sh`, `run-emulator-tablet-7.sh`, `run-emulator-tablet-10.sh`):
1. Checks for AVD existence and APK at `app/build/outputs/apk/release/app-release.apk`.
2. Starts the emulator with `-no-snapshot-save` (clean state each time).
3. Waits for boot: `adb wait-for-device`, then polls `adb shell getprop sys.boot_completed` until it returns `1`.
4. Installs the APK via `adb install -r` (replace existing).
5. Pushes a test PDF to `/sdcard/Download/` on the device.
6. Prints instructions for taking screenshots and changing locale.

**RAM tier emulators** (`run-emulator-ram500m.sh` through `run-emulator-ram10.sh`):

Same boot/install flow as screenshot emulators, but with an additional `-qemu -m ${MB}` flag that constrains the emulator's total RAM via QEMU. Example: `emulator -avd ram_500mb -no-snapshot-save -qemu -m 500`. The low-RAM scripts include a tip about resetting probe data: `adb shell pm clear com.svobodajakub.pdfg4compressor` (clears SharedPreferences, forcing the memory probe to re-run on next launch).

### 37.3 Locale Switching

`change-locale.sh` switches the emulator's locale for taking screenshots in different languages:

```bash
adb shell "setprop persist.sys.locale $LOCALE; setprop ctl.restart zygote"
```

This sets the system locale property and restarts the Zygote process (which restarts all Android framework services and apps). After ~10 seconds, the app is force-stopped via `adb shell am force-stop com.svobodajakub.pdfg4compressor` to ensure it relaunches with the new locale.

The script accepts a locale code as a command-line argument (`./change-locale.sh de-DE`) or prompts interactively. It lists 22 common locale codes for quick reference (en-US, de-DE, es-ES, fr-FR, it-IT, pt-BR, cs-CZ, sk-SK, pl-PL, ru-RU, uk-UA, zh-CN, zh-TW, ja-JP, ko-KR, ar-SA, he-IL, tr-TR, hi-IN, ta-IN, th-TH, vi-VN, id-ID). If only a language code is given without a country (e.g., `de`), the country is auto-derived by uppercasing the language code (e.g., `de-DE`).

### 37.4 Generated Documentation Files

`build-apk.sh` generates four documentation/helper files into `android-build/`:

| File | Purpose |
|---|---|
| `BUILD-FORMATS.md` | Explains the difference between APK and AAB formats, when to use each, and how to build both. |
| `QUICK-START.txt` | Condensed step-by-step guide for taking Google Play screenshots: emulator setup, APK installation, locale switching, screenshot capture workflow. |
| `QUICK-UPLOAD.txt` | Google Play Console upload checklist: AAB location, required listing fields, screenshot requirements, data safety answers. |
| `SCREENSHOTS-README.md` | Comprehensive screenshot automation documentation: AVD descriptions, emulator commands, locale list, screenshot naming conventions, desktop save configuration. |

These files are informational only — they are not used by the build process or the application.

### 37.5 Google Play Publishing

Publishing workflow:
1. Create Play Console account ($25 one-time fee, identity verification).
2. Create app listing with: short description, full description, icon-512.png, 2-8 screenshots, category "Productivity".
3. Privacy policy URL: `https://github.com/SvobodaJakub/pdf-to-g4-compressor/blob/main/src/privacy_policy.md`
4. Data safety: "No data collected".
5. Content rating questionnaire result: "Everyone".
6. Upload AAB from `android-build/app/build/outputs/bundle/release/app-release.aab`.

To release an update: increment `VERSION_CODE` (must increase by at least 1) and update `VERSION_NAME` in `build-apk.sh`, rebuild, upload new AAB.

**Annual requirement**: Google Play requires updating `targetSdk` to the latest API level within approximately 12 months of each new Android release. This is a one-line change in `build-apk.sh` (currently `targetSdk 35`) followed by a rebuild and upload. No other changes are required.

### 37.6 Gradle Dependencies

```groovy
implementation 'androidx.webkit:webkit:1.7.0'
implementation 'androidx.activity:activity:1.9.0'
implementation 'androidx.core:core:1.13.0'
constraints {
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.0")
}
```

The Kotlin stdlib constraint resolves duplicate class errors from transitive dependencies.

---

## 38. Input Hint Box

The input hint box (`#inputHintBox`) is a dismissible warning shown below the upload area when the selected file may not compress well.

### 38.1 Trigger Conditions

The hint is shown when:
- `totalPageCount > 50` (large document, likely already optimized)
- `inputFileSize > 100 MB` (very large file)
- `bytesPerPage < 150 KB` (low bytes per page suggests already-compressed content)
- ZIP mode with `maxPagesPerPDF > 50`
- After conversion result with compression ratio ≥ 0.9 (file barely shrank)

### 38.2 Content

The hint text explains that the app is designed for scanned paper documents, warns about re-encoding already-compressed content (generation loss), and advises compressing original un-optimized scans.

---

## 39. Page Count Limit

`pagesOver = totalPageCount > 500` — documents with more than 500 pages require the RAM override checkbox to enable the Compress button, regardless of estimated memory usage. This provides a safety net for extremely large documents where the RAM estimate may undercount.

---

## 40. JBIG2 PDF File Format Details

### 40.1 JBIG2 File Header

The JBIG2 file header parsed by `jbig2pdf.js`:
- 8-byte magic: `0x97 0x4A 0x42 0x32 0x0D 0x0A 0x1A 0x0A`
- Header flags byte determines organization (sequential vs random-access)
- Page count field (4 bytes, big-endian) when multi-page flag is set

### 40.2 Segment Parsing

Each JBIG2 segment has:
- 4-byte segment number
- 1-byte flags (segment type in bits 0-5, page association size in bit 6, deferred flag in bit 7)
- Referred-to segment count and references
- Page association number
- Data length (4 bytes)

Segment type 48 = page information segment (contains page width/height at offset +0/+4 as 4-byte big-endian integers). Segment type 49 = end-of-page marker.

### 40.3 PDF JBIG2 Stream Structure

Each page's stream uses:
- `/Filter /JBIG2Decode`
- `/DecodeParms << /JBIG2Globals N 0 R >>` referencing the global symbol dictionary stream
- `/ColorSpace [/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]`
- `/Decode [0 1]`

---

## 41. GitHub Corner Visibility

The GitHub corner link (top-right SVG) has special visibility logic:

- **Browser**: Always visible.
- **Android app**: Hidden initially (`style.display = 'none'`).
- **Shown when**: About, License, or Privacy modal is opened. Once shown, it stays visible for the rest of the session.
- **Hidden again on**: `resetAppState()` call.
- **Effect on joke locales**: Joke locales (FE, 67) are only shown in the language selector when the GitHub corner is visible OR it is April 1st. So in the Android app, opening any modal reveals both the GitHub link and the joke locales.

---

## 42. Flat Earth Animation Technical Details

### 42.1 3D Projection

#### 42.1.1 Projection

`feProjectPoint(x, y, z)` applies a perspective projection with a tilted camera:

```javascript
var cosA = 0.5299, sinA = 0.848; // cos(58°), sin(58°) precomputed
var rx = x - 170, ry = y - 170;  // center at (170, 170)
var ry2 = ry * cosA - z * sinA;  // rotate around X axis by 58°
var rz2 = ry * sinA + z * cosA;
var scale = 600 / (600 - rz2);   // perspective division (distance = 600)
return { x: 170 + rx * scale, y: 170 + ry2 * scale };
```

The camera looks down at the disc at 58° from horizontal, giving the isometric appearance. Perspective distance 600 provides mild foreshortening. The projection center is (170, 170) — the center of the 340×500 canvas area.

**Key geometry constants:**

| Constant | Value | Purpose |
|---|---|---|
| Disc radius (R) | 170 px | The circular disc spans 0–340 horizontally, centered at 170 |
| Disc thickness | 28 units | z=0 (bottom) to z=28 (top face) |
| Disc center Z | 14 | Midpoint of thickness; used as reference in `feComputeEdges` |
| Projection center | (170, 170) | Origin for the projection math |
| Perspective distance | 600 | Controls depth foreshortening |

#### 42.1.2 Edge Computation

`feComputeEdges()` samples 120 points around the disc circumference (N=120, evenly spaced by angle) and projects each at z=0 (bottom edge) and z=28 (top edge). Points where the bottom projection is below the top projection (`bot.y > top.y`) are the visible silhouette edges. These are classified as:

- **Front edges**: points below the projected disc center (`bot.y > projCenter.y`) — where the waterfall particles spawn in front of the disc.
- **Back edges**: points above the center — where particles spawn behind the disc.

Returns `{front: [{x,y}...], back: [{x,y}...], cx, cy}` where `cx`, `cy` is the projected center point.

#### 42.1.3 World Map SVG

`feCreateWorldSVG()` generates an inline SVG (`viewBox="0 0 100 100"`) cached after first call. Structure:

1. **Clip path**: circular clip `<circle cx=50 cy=50 r=48>` — constrains everything to the disc face.
2. **Ocean**: 3 concentric filled circles creating a depth gradient:
   - r=49, fill `#1565a0` (deepest blue)
   - r=47, fill `#1a78b8` (mid blue)
   - r=44, fill `#1e88c8` (lightest blue)
3. **Land masses**: 121 SVG path elements from `FE_LAND_PATHS` (injected from `flatearth-paths.json` at build time, section 3.1 step 5). Each filled `#3a7228` (green), stroked `#2d5a1e` (darker green), stroke-width 0.15.
4. **Polar ice cap**: `<circle cx=50 cy=50 r=4.5>` filled `#dce8f2`, opacity 0.4. The North Pole is at the center of an azimuthal equidistant projection.
5. **Border rings**: inner ring r=47 stroked `rgba(220,235,250,0.15)` width 2; outer ring r=48 stroked `rgba(200,220,240,0.2)` width 0.6.

#### 42.1.4 Disc Construction

`feCreateDisc(container, worldSVG)` builds the DOM for one flat earth disc:

1. **Wrapper** (`div.fe-world-wrapper`): 340×500 px, `will-change: transform` for GPU compositing.
2. **Back canvas** (`canvas.fe-water-back`): 340×500, z-index 1. Particle waterfall behind the disc.
3. **World div** (`div.fe-world`): 340×340, `perspective: 600px`. Contains:
   - **Slab** (`div.fe-slab`): `transform: rotateX(58deg)`. Contains:
     - 5 **side rings** (`div.fe-side`): each at a different `translateZ` (z = 0, 5.6, 11.2, 16.8, 22.4). Colors computed from: `r = 115 - 35*t`, `g = 95 - 30*t`, `b = 65 - 25*t` for t ∈ {0, 0.2, 0.4, 0.6, 0.8}. Each has a 1px border slightly darker than its fill.
     - **Top face** (`div.fe-top`): `translateZ(28px)`, `border-radius: 50%`, contains the world map SVG.
     - **Sun orbit** (`div.fe-sun-orbit`): CSS animation with randomized duration `7 + Math.random() * 4` seconds (7–11s). Contains `div.fe-sun` (14×14 px radial gradient, golden glow, `translateZ(35px)` — orbits above the disc).
4. **Front canvas** (`canvas.fe-water-front`): 340×500, z-index 3. Particle waterfall in front of the disc.

Returns `{wrapper, canvasBack, canvasFront}`.

### 42.2 Particle System

Class `FEWater` manages the two-layer particle waterfall for one disc. Initialized with references to the back and front canvases and the edge points from `feComputeEdges()`.

#### 42.2.1 Spawning

`FEWater.prototype.spawn(edgePoints, particles)` — selects a random edge point and creates a particle:

```javascript
{
    x: ep.x + (Math.random()-0.5)*1.5,   // position with ±0.75 px jitter
    y: ep.y + (Math.random()-0.5)*1.5,
    vx: (dx/len)*0.35 + (Math.random()-0.5)*0.1,  // outward from center + random spread
    vy: 0.5 + Math.random()*0.5,         // downward: 0.5 to 1.0 px/frame
    life: 1.0,                            // starts at full life
    size: 0.5 + Math.random()*0.8         // radius: 0.5 to 1.3 px
}
```

Where `dx = ep.x - center.x`, `dy = ep.y - center.y`, `len = sqrt(dx² + dy²)`. The velocity pushes particles outward and downward from the disc edge.

**Spawn rate per frame**: 10 front particles + 4 back particles = 14 total per `requestAnimationFrame` tick.

#### 42.2.2 Physics Update

`FEWater.prototype.update()`:

```javascript
p.x += p.vx;
p.y += p.vy;
p.vy += 0.03;     // gravity acceleration (pixels/frame²)
p.life -= 0.008;   // life decay per frame
```

Particles are removed when `life <= 0` or `y > 500` (below canvas). Removal uses `splice(i, 1)` during a reverse iteration.

#### 42.2.3 Rendering

`FEWater.prototype.drawLayer(ctx, particles)`:

1. Clears the canvas: `ctx.clearRect(0, 0, 340, 500)`.
2. For each particle:
   - Alpha: `Math.min(p.life * 0.6, 0.5)` — fades from 0.5 to 0 as life decreases. Capped at 0.5 (never fully opaque).
   - Color: indexed from `fePalette[Math.min(Math.round(p.life * 20), 20)]`. The palette has 21 pre-computed entries: `hsl(200, 75%, 50%)` through `hsl(200, 75%, 70%)`. Living particles are lighter; dying particles are darker.
   - Shape: filled circle at `(p.x, p.y)` with radius `p.size`.

`draw()` calls `drawLayer` for both back and front canvases. `clear()` is an optimization that only clears canvases if particles exist (avoids unnecessary `clearRect` calls on offscreen discs).

### 42.3 Layout

`feInit()` creates a tiling grid of flat earth discs that drift across the screen.

#### 42.3.1 Grid Configuration

| Constant | Value | Purpose |
|---|---|---|
| `cellW` | 900 px | Horizontal spacing between disc centers |
| `cellH` | 750 px | Vertical spacing between disc centers |
| `cols` | 2 | Grid columns |
| `rows` | 3 | Grid rows |
| Total discs | 6 | 2 × 3 grid |

The tile dimensions are expanded to at least cover the viewport plus margin: `tileW = max(cols*cellW + cellW/2, innerWidth + cellW + 400)`, `tileH = max(rows*cellH, innerHeight + cellH + 500)`.

**Hex offset**: Odd rows are offset by `cellW/2` horizontally, creating a honeycomb pattern.

**Random initial offset**: `gridOffX = Math.random() * tileW`, `gridOffY = Math.random() * tileH` — randomizes the starting position so the grid doesn't always begin at the same spot.

**Per-disc random opacity**: `0.65 + Math.random() * 0.25` (range 0.65–0.9).

#### 42.3.2 Animation Loop

`requestAnimationFrame`-driven loop:

1. Compute `dt = (now - lastTime) / 1000` seconds, capped at 0.1s (prevents large jumps if tab was backgrounded).
2. Move each disc: `d.x += vx * dt`, `d.y += vy * dt` where `vx = 22` px/s, `vy = 15` px/s (slow diagonal drift toward bottom-right).
3. **Tile wrapping**: when `d.x > tileW`, subtract `tileW`; when `d.y > tileH`, subtract `tileH`. This creates seamless infinite tiling.
4. Apply CSS transform: `translate({x - offX}px, {y - offY}px)`.
5. **Visibility culling**: A disc is visible if its screen position is within `(-400, screenW) × (-500, screenH)`. Offscreen discs are not updated — their `FEWater.clear()` is called instead of `update()`+`draw()`, freeing CPU from animating invisible particles.

### 42.4 Performance

- `will-change: transform` hint for GPU acceleration
- Sun orbit animation with randomized duration (7-11 seconds)
- Separate front/back canvas layers for depth ordering

---

## 43. Rendering Pipeline Details

### 43.1 Page Rendering Flow

For each page in `renderPDFPages()`:

1. Get page viewport at scale 1.0 from PDF.js.
2. Optionally compute rotated viewport for rotation preservation.
3. Calculate scale factor: `Math.min(targetWidth/viewportWidth, targetHeight/viewportHeight)`.
4. Create temporary off-screen canvas at scaled viewport dimensions.
5. Fill with white, render PDF page via `page.render()`.
6. Create destination canvas at target page size (e.g., 2566×3629 for A4 at 310 DPI).
7. Fill with white, composite temp canvas centered on destination.
8. Free temp canvas (`width = 0; height = 0`).
9. Extract ImageData, free destination canvas.
10. Run `processImage()` to get bilevel data.
11. Fill imageData with zeros (help GC).
12. G4 path: invert, encode with G4Encoder, push page object.
13. JBIG2 path: write PBM to WASM FS, null bilevel data, push metadata-only page object.
14. Call `page.cleanup()`.

### 43.2 PDF Loading Timeout

`loadPDFWithTimeout(data, timeoutMs)` wraps `pdfjsLib.getDocument()` with a timer. ZIP mode uses 5-second timeout per PDF. Single PDF mode uses 10-second timeout. This prevents hanging on corrupt PDFs.

---

## 44. Result Box Color Coding

| Compression Ratio | Background | Border | Text Color | Interpretation |
|---|---|---|---|---|
| < 0.6 (< 60%) | #d4edda (green) | #c3e6cb | #155724 | Good compression |
| 0.6 - 1.0 | #fff3cd (yellow) | #ffeaa7 | #856404 | Poor compression |
| > 1.0 | #ffe5cc (orange) | #ffb366 | #8B4513 | File grew larger |

For ratios ≥ 0.6, additional context messages are shown explaining that the app is designed for scanned documents and suggesting the file may already be optimized. If dithering was used and results are poor, a note suggests trying without dithering.

---

## 45. Architecture Decision: Why Pure JavaScript

Four implementation approaches were evaluated before this architecture was chosen:

| Approach | File Size | Init Time | Build Complexity | Performance | Verdict |
|---|---|---|---|---|---|
| Full WASM (GraphicsMagick + Ghostscript + Python compiled to WASM) | 50-100 MB | 5-15s | Extreme (weeks-months) | 30-50% of native | Rejected |
| Linux VM (v86 x86 emulator running full Linux + native tools) | 35-110 MB | 30-60s boot | High | 1-2% of native (50-100x slower) | Rejected |
| Hybrid WASM (CCITT encoder in WASM, rest in JS) | ~3 MB | <1s | Low-moderate | 2-5x faster encoding | Considered but unnecessary |
| Pure JavaScript (port G4Enc to JS, use PDF.js, pako) | ~2.7 MB | Instant | None (no compiler toolchain) | Good (encoding is not the bottleneck) | Chosen |

The only component later compiled to WASM was jbig2enc (added after the initial pure-JS architecture was proven), because JBIG2 symbol matching has no reasonable pure-JS equivalent. The G4 encoder, image processing, PDF generation, and PDF compression remain pure JavaScript.

Key insight: the performance bottleneck is PDF.js rendering (CPU-bound canvas operations), not compression encoding. G4 encoding takes ~1-2 ms per page. Optimizing it with WASM would provide no user-visible speedup.

---

## 46. Detailed Algorithm Specifications

This section documents exact constants, algorithms, and thresholds that are load-bearing for correct behavior. Visual/CSS details (colors, gradients, animation keyframe values, pixel sizes) are intentionally omitted — they are aesthetic and can be chosen freely by a reimplementation.

### 46.1 Locale Detection Algorithm (i18n.js)

```
function detectLanguage():
  for each locale in (navigator.languages || [navigator.language || navigator.userLanguage || 'en']):
    locale = normalizeBCP47(locale)
    if TRANSLATIONS[locale] exists: return locale
    if LOCALE_FALLBACK[locale] exists and TRANSLATIONS[that] exists: return that
    baseLang = locale.split('-')[0]
    if TRANSLATIONS[baseLang] exists: return baseLang
  return 'en'
```

`normalizeBCP47(tag)` splits on `-`, lowercases the first part (language), titlecases 4-character parts (script subtags like `Hans`, `Mong`, `Cyrl`), uppercases 2-character parts (region subtags like `CN`, `US`), lowercases everything else.

Deprecated Android locale codes: Android's Java `Locale` class rewrites `he→iw`, `id→in`, `yi→ji` regardless of Android version, and the WebView's `navigator.language` inherits these deprecated codes. The `LOCALE_FALLBACK` table contains entries mapping the deprecated codes and their regional variants back to the modern codes used by `TRANSLATIONS`: `'iw': 'he'`, `'iw-IL': 'he'`, `'in': 'id'`, `'in-ID': 'id'`, `'ji': 'yi'`. Desktop browsers report the modern codes (`he`, `id`, `yi`) directly, so the fallback entries are only exercised in the Android WebView. The Android locale resource generator (section 36) performs the reverse mapping (`he→iw`, `id→in`, `yi→ji`) for resource directory naming.

### 46.2 LOCALE_FALLBACK Table

The complete mapping (regional variant → canonical key in TRANSLATIONS):

```
German:    de-AT, de-CH, de-BE, de-LI → de
English:   en-GB, en-US, en-AU, en-NZ, en-CA, en-IN, en-ZA → en
Spanish:   es-MX, es-AR, es-CO, es-CL, es-PE, es-VE → es
Portuguese: pt-BR, pt-PT → pt
French:    fr-CA, fr-BE, fr-CH → fr
Chinese:   zh → zh-Hans (plain zh defaults to Simplified)
           zh-CN, zh-SG, zh-Hans-CN, zh-Hans-SG → zh-Hans
           zh-TW, zh-HK, zh-MO, zh-Hant-TW, zh-Hant-HK → zh-Hant
Arabic:    ar-EG, ar-SA, ar-MA, ar-DZ, ar-TN, ar-SY, ar-IQ → ar
Swedish:   sv-SE, sv-FI → sv
Norwegian: nb-NO → nb; nn-NO → nn; no-NO → nb
Polish:    pl-PL, pl-US → pl
Urdu:      ur-PK, ur-IN → ur
Punjabi:   pa-IN, pa-PK → pa
Indonesian: id-ID → id
Deprecated Android codes: iw, iw-IL → he; in, in-ID → id; ji → yi (Android Java Locale rewrites he/id/yi to deprecated codes; WebView inherits them)
Tagalog:   tl-PH, fil-PH, fil → tl (Android uses 'fil')
Vietnamese: vi-VN → vi
Thai:      th-TH → th
Azerbaijani: az-AZ → az
Uzbek:     uz-UZ → uz
Kazakh:    kk-KZ → kk
Georgian:  ka-GE → ka
Armenian:  hy-AM → hy
Belarusian: be-BY → be
Mongolian: mn-MN → mn; mn-Mong-MN, mn-Mong-CN → mn-Mong
Amharic:   am-ET → am
Sinhala:   si-LK → si
Bosnian:   bs-BA → bs
Macedonian: mk-MK → mk
Croatian:  hr-HR, hr-BA → hr
Serbian Cyrillic: sr, sr-RS, sr-BA, sr-ME, sr-Cyrl-RS, sr-Cyrl-BA, sr-Cyrl-ME → sr-Cyrl
Serbian Latin: sr-Latn-RS, sr-Latn-BA, sr-Latn-ME → sr-Latn; sh → sr-Latn
Catalan:   ca-ES, ca-AD → ca
Basque:    eu-ES → eu
Tibetan:   bo-CN, bo-IN → bo
Joke:      en-FE → en-FE, cs-FE → cs-FE, sk-FE → sk-FE, 67 → 67
```

### 46.3 applyTranslations Algorithm

```
function applyTranslations(lang):
  t = TRANSLATIONS[lang] || TRANSLATIONS.en
  document.documentElement.lang = lang
  set body dir="rtl" if lang in {ar, he, ur, yi}, else "ltr"
  for each element with data-i18n attribute:
    key = element.getAttribute('data-i18n')
    if t[key]:
      if element is INPUT with type="text": set placeholder
      else: set textContent
  for each element with data-i18n-template attribute:
    key = that attribute
    if t[key]: store t[key] in data-i18n-template-text attribute
```

The `data-i18n-template` mechanism stores a template string on the element; JavaScript code later replaces `{placeholders}` with runtime values (used for DPI dimension display).

### 46.4 Core vs Additional Translations

`i18n.js` contains the TRANSLATIONS object with 6 languages inline: en, de, es, pt, cs, sk. It ends with the marker `// Continue in next file due to length...`. `i18n-languages.js` contains `ADDITIONAL_TRANSLATIONS` with all remaining languages. During build, the additional translations are spliced into TRANSLATIONS by replacing the marker.

### 46.5 Memory Probe Timing Constants

| Phase | Duration | Notes |
|---|---|---|
| Phase 1 (JS allocation in WebView) | 8 seconds | Timer starts on `ProbeSignal.ready()` callback from JS |
| Phase 2 (Java heap allocation) | 16 seconds allocation + 10 seconds hold = 26 seconds | `PHASE2_DURATION_MS = 16000` |
| Wait between failed 1400 MB and 800 MB probe | 5 seconds | Grey spinner shown |
| Post-probe delay before loading app | 3 seconds | Grey spinner, lets OS reclaim memory |
| JS-ready timeout (fallback) | 60 seconds | If JS never signals ready, treat as failure |

The `ProbeSignalInterface` Java class registers as `"ProbeSignal"` in the WebView. The probe HTML calls `ProbeSignal.ready()` after loading, which triggers the phase 1 timer on the UI thread. If the signal never arrives within 60 seconds, the probe is treated as failed.

### 46.6 Calibration Screen Details

The calibration screen shows a `FrameLayout` with:
- "First launch, calibrating..." text label (from `R.string.calibrating`)
- A `ProgressBar` spinner (initially 120×120 px, enlarged to 180×180 px when phase 2 starts — raw pixel `LayoutParams`, not dp)
- Random black dots: grid of 20 columns × 50 rows, dot size 30% of cell size, maximum 60 dots on screen (oldest removed when exceeded), new dot added every 300 ms

### 46.7 DPI Warning Thresholds

```
if estimatedRAM > RAM_LIMIT:  → "Critical" warning (red), compress button blocked
else if estimatedRAM > 400 MB: → "High" warning (yellow), compress button NOT blocked
else if DPI < 200 (no-dither) or DPI < 240 (dither): → "Low quality" warning
```

The 400 MB threshold is hardcoded and independent of the memory tier.

### 46.8 DPI Auto-Adjustment Threshold

`autoAdjustDPI()` only switches to Custom DPI mode if `findMaxSafeDPI()` returns ≥ 200. Below 200 DPI, auto-adjustment does nothing and leaves the DPI unchanged. This prevents auto-selecting an unusably low DPI.

### 46.9 AI Auto-Setter Trial Generation

DPI levels are computed as:
1. Standard tiers filtered by max safe DPI: [310, 250, 216] (only those ≤ maxSafeDPI).
2. If maxSafeDPI < 216 and ≥ 144: add maxSafeDPI itself, plus `max(round(maxSafeDPI × 0.75), 144)` as a lower step.

For each DPI level (index `dli`, total count `N`):
```
trials.push(dithered G4)                           // all DPI levels
if dli == 0: trials.push(dithered JBIG2 t=0.97)   // highest DPI only
trials.push(dithered JBIG2 t=0.85)                 // all DPI levels
if dli == N-1:                                      // lowest DPI only
    trials.push(undithered G4)
    trials.push(undithered JBIG2 t=0.85)
```

Trials that exceed RAM_LIMIT or JBIG2 feasibility limits are filtered out before execution. The AI always enables rotation preservation and includes producer/timestamp metadata.

### 46.10 AI Progress EMA Constants

| Constant | Value | Purpose |
|---|---|---|
| BOOTSTRAP_SECS | 6 | Seconds of synthetic curve before real data takes over |
| Bootstrap curve | `3 + 9 * (1 - exp(-2.5 * t))` | Starts at 3%, asymptotes to 12% |
| Bootstrap blend | `t²` | 0 = fully synthetic, 1 = fully real |
| Display EMA tau | 2.0 s | Smoothing for progress bar position |
| Rate EMA tau | 8.0 s | Smoothing for progress rate estimation |
| ETA EMA tau | 10.0 s | Smoothing for remaining time estimate |
| JBIG2 encoding tau | `max(numPages × 0.5, 8)` seconds | Asymptotic interpolation for encoding phase (no page-level progress) |
| Display clamp | 99.5% max | Prevents bar from reaching 100% prematurely |

### 46.11 cleanupPreviousResult Preservation

When `cleanupPreviousResult()` runs and `progressBoxState` was not null (meaning Advanced Tricks was visible), it preserves the section: sets `progressBoxState = 'cancelled'`, adds `.cancelled` class, rebuilds Advanced Tricks HTML with `buildAdvancedTricksHTML(false)`, and attaches listeners. This ensures JBIG2/rotation/metadata checkboxes persist across file re-selection. If `progressBoxState` was null (first file selection), the progress div is hidden entirely.

### 46.12 downloadFile Pre-Save Cleanup

Before the save operation, `downloadFile()`:
1. Calls `initJBIG2Module()` to destroy and recreate WASM instance (frees heap).
2. Zeros the preview canvas backing store.
3. (Android path) Streams data to Java in 768 KB chunks, each base64-encoded.
4. Nulls `window.resultPDF` and `data` in JS before calling `endSave()`.
5. (Tier 1/2 only) Nulls `selectedFile`, `window.resultFilename`, `window.originalSize`, `window.resultSize`, `window.ditherMode`, `resultUsedJBIG2`, `totalPageCount`, `maxPagesPerPDF`, `inputFileSize`.
6. Calls `saveAppState()` to snapshot the current form state before the WebView might be destroyed.

### 46.13 App Self-Download Encoding (Android)

For Android: `btoa(unescape(encodeURIComponent(html)))` — this three-step chain converts the UTF-8 HTML string to a binary-safe base64 string that the Java `saveFile()` method can decode. For browser: direct `Blob` creation from the string.

### 46.14 validateFormMatchesResult Field Mapping

The save button is enabled only when all 10 fields match:

| Form control | resultSettings field | Transform |
|---|---|---|
| selectedFile.name | fileName | exact |
| mode radio value | ditherMode | 'no-dither'→'none', 'dither'→'all', 'dither-selected'→'selected' |
| pageRange input (when selected) | pageRange | parsed via parsePageRange(), re-joined with commas |
| standard radio checked ? 310 : slider | dpi | integer |
| pageSize radio value | pageSize | exact |
| useJBIG2 checkbox | useJBIG2 | boolean |
| jbig2Threshold radio value | jbig2Threshold | parseFloat |
| preserveRotation checkbox | preserveRotation | boolean |
| includeProducer checkbox | includeProducer | boolean (`?? true` default) |
| includeTimestamp checkbox | includeTimestamp | boolean (`?? true` default) |

### 46.15 LANGUAGE_NAMES Constant

The language selector modal uses a `LANGUAGE_NAMES` constant mapping all 83+ language codes to their native display names (e.g., `'de': 'Deutsch'`, `'ja': '日本語'`, `'mn-Mong': 'ᠮᠣᠩᠭᠣᠯ'`, `'67': 'brainrot'`, `'en-FE': 'English (Flat Earth)'`). This constant is defined inside the DOMContentLoaded handler in build.py and populated by the language selector population function.

### 46.16 Joke Locale Visibility (Exact Logic)

```
const isAprilFirst = (month === 3 && day === 1);  // JS months are 0-indexed
const githubVisible = (githubCornerElement && githubCornerElement.style.display !== 'none');
const showJokes = isAprilFirst || githubVisible;
```

If `showJokes` is false, languages whose code ends with `-FE` or equals `67` are excluded from the language selector grid.

### 46.17 Chunked File Restoration

When restoring state from Android (section 23.4), the file is read in 768 KB chunks via `AndroidFileHandler.readRestoredFileChunk(offset, CHUNK)`. Each chunk returns a base64 string which is decoded to a Uint8Array. All chunks are concatenated into a single Uint8Array, then wrapped in a `File` object via `new File([combined], fileName, {type: mimeType})`. The Java-side byte array is then freed via `clearRestoredFile()`.

### 46.18 Probe HTML Content

The probe HTML loaded into the WebView during calibration is generated by `makeProbeHtml(megabytes)`:
1. Calls `ProbeSignal.ready()` via the registered JavaScript interface.
2. Allocates `megabytes` MB of `Uint32Array`s (each 1 MB = 262144 entries), filled with random data via `Math.random()`.
3. Runs a periodic function (every 500 ms) that reads one value from every 512th position in every array, keeping the data touched so the OS cannot page it out.

### 46.19 File Size Guard (fileSizeOver)

`fileSizeOver = inputFileSize > 175 * 1048576` (175 MB). This is a fast early-out redundant with the RAM estimation formula. When true, the RAM override checkbox is required to enable the Compress button, along with `pagesOver` (> 500 pages) and `ramOver` (estimated RAM > RAM_LIMIT).

---

## 47. Code Wiring and Control Flow

This section documents the exact control flow, function signatures, DOM element IDs, and code generation patterns that connect the pieces described in earlier sections. Without this, a reimplementation would know *what* to build but not *how the parts are wired*.

### 47.1 Compress Button Click Handler (full flow)

The compress button is a `div#convertBtn[role="button"]` (not an HTML `<button>`). The click handler is an async function:

```
async click handler:
  hide AI/refresh boxes
  if (!selectedFile) return
  if (conversionInProgress) { cancellationRequested = true; return }
  if (convertBtn has class 'disabled') return

  // Read Advanced Tricks checkboxes BEFORE destroying them
  read useJBIG2, jbig2Threshold, preserveRotation, includeProducer, includeTimestamp
    from DOM elements (IDs: useJBIG2, jbig2Threshold097/092/085, preserveRotation,
    includeProducer, includeTimestamp)
  read ditherMode from input[name="mode"]:checked .value
  parse page range if ditherMode is 'dither-selected'

  // Save Advanced Tricks into resultSettings (for recovery if error occurs)
  resultSettings.preserveRotation = preserveRotationForThisRun
  resultSettings.includeProducer = includeProducerForThisRun
  (etc.)

  conversionInProgress = true
  cancellationRequested = false
  document.body.classList.add('converting')
  saveAppState()          // before deepCleanMemory destroys DOM
  deepCleanMemory()       // frees prior results, zeros canvases, reinits JBIG2

  try {
    // Reset progress div to spinner + "Processing..."
    progressDiv.innerHTML = '<span class="spinner"></span><span id="progressText">...</span>'
    progressDiv.style.display = 'block'
    progressText = document.getElementById('progressText')  // re-acquire reference
    setFormControlsEnabled(false)

    targetDPI = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value)
    pageSize = document.querySelector('input[name="pageSize"]:checked').value
    metadataOpts = { includeProducer: ..., includeTimestamp: ... }

    if (isZipMode)
      await convertZIP(selectedFile, ditherConfig, targetDPI, pageSize,
                        useJBIG2, jbig2Threshold, preserveRotation, metadataOpts)
    else
      await convertPDF(selectedFile, ditherConfig, targetDPI, pageSize,
                        useJBIG2, jbig2Threshold, preserveRotation, metadataOpts)
  } catch (error) {
    if (error.message === 'CONVERSION_CANCELLED')
      showCancelledBox()
    else
      errorRecoveryNeeded = true
  } finally {
    conversionInProgress = false
    cancellationRequested = false
    document.body.classList.remove('converting')
    setFormControlsEnabled(true)
    if (errorRecoveryNeeded) await recoverFromError()
    updateCompressButton()
  }
```

Cancellation is checked inside `renderPDFPages()` between each page: `if (cancellationRequested) throw new Error('CONVERSION_CANCELLED')`. This exception propagates up through `convertPDF`/`convertZIP` to the catch block above.

### 47.2 Key DOM Element IDs

These IDs are referenced by JavaScript and must match between template.html and build.py:

| Element | ID | Type | Notes |
|---|---|---|---|
| File input | `pdfFile` | `<input type="file">` | Hidden, triggered by label |
| Upload area | `uploadArea` | `<div>` | Drag-and-drop target |
| Filename display | `filename` | `<div>` | Shows selected filename |
| File info | `fileInfo` | `<div>` | Shows page count + file size |
| Convert button | `convertBtn` | `<div role="button">` | Not a `<button>` element |
| Progress container | `progress` | `<div>` | Shows spinner/result/cancelled |
| Progress text | `progressText` | `<span>` | Inside progress div, recreated on each conversion |
| DPI standard radio | `dpiStandard` | `<input type="radio">` | name="dpiMode" |
| DPI custom radio | `dpiCustom` | `<input type="radio">` | name="dpiMode" |
| DPI slider | `dpiSlider` | `<input type="range">` | min=72 max=1200 |
| DPI value input | `dpiValue` | `<input type="number">` | Synced with slider |
| DPI slider container | `dpiSliderContainer` | `<div>` | Shown/hidden via `.show` class |
| DPI warning | `dpiWarning` | `<div>` | Shows RAM/quality warnings |
| Page range input | `pageRange` | `<input type="text">` | For dither-selected mode |
| Page range container | `pageRangeContainer` | `<div>` | Shown/hidden via `.show` class |
| Dither-selected radio | `ditherSelected` | `<input type="radio">` | name="mode", value="dither-selected" |
| No-dither radio | `noDither` | `<input type="radio">` | name="mode", value="nodither" |
| Dither radio | `dither` | `<input type="radio">` | name="mode", value="dither" |
| Use English checkbox | `useEnglishCheckbox` | `<input type="checkbox">` | |
| Mongolian checkbox | `useMongolianCheckbox` | `<input type="checkbox">` | |
| Language switch container | `languageSwitch` | `<div>` | Shown via `.show` class |
| Mongolian switch container | `mongolianSwitch` | `<div>` | Shown via `.show` class |
| Preview canvas | `previewCanvas` | `<canvas>` | Hidden, used for rendering |
| Help button | `helpBtn` | `<button>` | Bottom-left corner |
| Language selector button | `languageSelectorBtn` | `<button>` | Bottom-left, above help |
| Input hint box | `inputHintBox` | `<div>` | Shown via `.show` class |
| License modal | `licenseModal` | `<div>` | role="dialog" |
| About modal | `aboutModal` | `<div>` | role="dialog" |
| Privacy modal | `privacyModal` | `<div>` | role="dialog" |
| Language modal | `languageModal` | `<div>` | role="dialog" |
| AI auto-setter | `aiAutoSetter` | `<div>` | Created dynamically by JS |
| AI refresh | `aiRefresh` | `<div>` | Created dynamically by JS |
| AI progress bar | `aiProgress` | `<div>` | Inside AI auto-setter |
| AI status text | `aiStatus` | `<div>` | Inside AI auto-setter |

Radio group names: `mode` (dither), `dpiMode`, `pageSize`, `jbig2Threshold`.

Page size radio values: `a4-portrait`, `a4-landscape`, `letter-portrait`, `letter-landscape`, `legal-portrait`.

Advanced Tricks elements (created dynamically inside progress div by `buildAdvancedTricksHTML()`): `advancedTricksToggle`, `advancedTricksContent`, `useJBIG2`, `jbig2ThresholdOptions`, `jbig2Threshold097`/`092`/`085`, `jbig2DisabledExplain`, `preserveRotation`, `includeProducer`, `includeTimestamp`, `ramOverrideContainer`, `ramOverride`, `saveResultBtn`.

Additional IDs used in template.html but not actively referenced by the inline application JavaScript (used for accessibility, modal structure, or secondary features):

| Element | ID | Type | Notes |
|---|---|---|---|
| Flat Earth background | `feBg` | `<div>` | Populated by `feInit()` |
| Privacy link | `showPrivacy` | `<a>` | Opens Privacy modal |
| License link | `showLicense` | `<a>` | Opens License modal |
| About link | `showAbout` | `<a>` | Opens About modal |
| Version display | `appVersion` | `<p>` | Shows `{app_version}` |
| Upload area label | `uploadAreaLabel` | `<label>` | `aria-labelledby` target for upload area |
| Conversion mode label | `conversionModeLabel` | `<span>` | `aria-labelledby` target for mode radiogroup |
| Page size label | `pageSizeLabel` | `<span>` | `aria-labelledby` target for pageSize radiogroup |
| Output DPI label | `outputDpiLabel` | `<span>` | `aria-labelledby` target for dpiMode radiogroup |
| Page range hint | `pageRangeHint` | `<div>` | `aria-describedby` target for page range input |
| License close button | `closeLicense` | `<button>` | Modal close |
| About close button | `closeAbout` | `<button>` | Modal close |
| Privacy close button | `closePrivacy` | `<button>` | Modal close |
| Language close button | `closeLanguageModal` | `<button>` | Modal close |
| License modal title | `licenseModalTitle` | `<h2>` | `aria-labelledby` target |
| About modal title | `aboutModalTitle` | `<h2>` | `aria-labelledby` target |
| Privacy modal title | `privacyModalTitle` | `<h2>` | `aria-labelledby` target |
| Source tarball toggle | `sourceToggle` | `<a>` | Expands source section in License modal |
| Source tarball content | `sourceContent` | `<div>` | Collapsible container |
| Source tarball textarea | `sourceTextarea` | `<textarea>` | Readonly, filled by JS with `SOURCE_TARBALL_BASE64` |
| Source tarball download | `sourceDownload` | `<a>` | Download link for base64 .txt file |
| Privacy toggle (About) | `privacyToggle` | `<a>` | Expands privacy section in About modal |
| Privacy content (About) | `privacyContent` | `<div>` | Collapsible container |
| App download toggle | `appDownloadToggle` | `<a>` | Expands self-download section in About modal |
| App download content | `appDownloadContent` | `<div>` | Collapsible container |
| App download button | `appDownloadBtn` | `<a>` | Self-download link |
| Language grid | `languageList` | `<div>` | Populated by `populateLanguageList()` |
| Debug preview | `debugPreview` | `<div>` | Hidden (`display:none`), development only |
| Debug preview info | `previewInfo` | `<div>` | Inside debug preview |
| A4 Portrait radio | `pageSizeA4Portrait` | `<input type="radio">` | name="pageSize", value="a4-portrait" |
| A4 Landscape radio | `pageSizeA4Landscape` | `<input type="radio">` | name="pageSize", value="a4-landscape" |
| Letter Portrait radio | `pageSizeLetterPortrait` | `<input type="radio">` | name="pageSize", value="letter-portrait" |
| Letter Landscape radio | `pageSizeLetterLandscape` | `<input type="radio">` | name="pageSize", value="letter-landscape" |
| Legal Portrait radio | `pageSizeLegalPortrait` | `<input type="radio">` | name="pageSize", value="legal-portrait" |

### 47.2.1 `mongolianRelevantRegions` Lists

The Mongolian checkbox is shown when the user's detected locale matches a "Mongolian-relevant region" (Mongolia or mainland China / Inner Mongolia). This check appears in two places with slightly different lists:

**DOMContentLoaded init** (determines whether to show the Mongolian checkbox on load):
```javascript
const mongolianRelevantRegions = ['mn', 'mn-MN', 'mn-Mong', 'mn-Mong-MN', 'mn-Mong-CN',
                                  'zh-CN', 'zh-Hans', 'zh-Hans-CN'];
```
8 entries. Does NOT include bare `'zh'`.

**Language selector click handler** (determines whether to show the Mongolian checkbox after the user switches language via the language selector modal):
```javascript
const mongolianRelevantRegions = ['mn', 'mn-MN', 'mn-Mong', 'mn-Mong-MN', 'mn-Mong-CN',
                                  'zh', 'zh-CN', 'zh-Hans', 'zh-Hans-CN'];
```
9 entries. DOES include bare `'zh'`.

The difference: bare `'zh'` (Chinese without a script/region subtag) is only matched in the language selector handler, not at init. In practice, the init path rarely sees bare `'zh'` because `detectLanguage()` resolves `'zh'` to `'zh-Hans'` via the `LOCALE_FALLBACK` table (section 46.2: `zh → zh-Hans`). The language selector handler includes it as an extra safety catch for edge cases where a user manually selects a language that produces `'zh'` as the current locale. This discrepancy is minor and does not cause user-visible bugs.

### 47.3 setFormControlsEnabled(enabled)

Disables/enables: `pdfFileInput.disabled`, `dpiSlider.disabled`, `pageRangeInput.disabled`, all radios in groups `mode`, `dpiMode`, `pageSize`. Uses the HTML `disabled` attribute (not CSS). On re-enable, also calls `updateZipModeUI()` if in ZIP mode (to re-disable the dither-selected radio).

### 47.4 Binary-to-Base64 Chunking (JS → Java)

Used in both `downloadFile()` (save) and the Android restore path (read). The pattern for encoding a Uint8Array to base64 in chunks:

```javascript
var CHUNK = 768 * 1024;
for (var off = 0; off < bytes.length; off += CHUNK) {
    var end = Math.min(off + CHUNK, bytes.length);
    var slice = bytes.subarray(off, end);
    var bin = '';
    for (var j = 0; j < slice.length; j++) {
        bin += String.fromCharCode(slice[j]);
    }
    AndroidFileHandler.writeChunk(btoa(bin));
}
```

The key detail: `String.fromCharCode` is called per-byte in a loop to build a binary string, then `btoa()` base64-encodes it. This avoids `Function.apply` stack overflow on large chunks.

### 47.5 build.py JBIG2 Glue Code Generation

build.py generates four JavaScript blocks for JBIG2 support. The key mechanism for storing the Emscripten loader source is `json.dumps()` in Python, which produces a JSON string literal (with all quotes, newlines, and special characters escaped). This JSON string is emitted as a JavaScript assignment:

```python
jbig2_js_json = json.dumps(jbig2_js_patched)  # Python json.dumps escapes the JS source
```

The generated JavaScript output (in the assembled `<script>` block) looks like:

```javascript
// 1. Decode WASM binary from base64
(function() {
    const jbig2WasmBase64 = '<base64 string>';
    const wasmBinary = atob(jbig2WasmBase64);
    const wasmBytes = new Uint8Array(wasmBinary.length);
    for (let i = 0; i < wasmBinary.length; i++) {
        wasmBytes[i] = wasmBinary.charCodeAt(i);
    }
    window._jbig2WasmBytes = wasmBytes;
})();

// 2. Store patched loader source as JSON-escaped string
window._jbig2LoaderSource = <json.dumps output>;  // e.g. "var Module=window.Module||{}; ..."

// 3. Create initial Module and run loader (first-time init)
window.Module = {
    wasmBinary: window._jbig2WasmBytes,
    noInitialRun: true,
    print: function(text) { console.log('[JBIG2]', text); },
    printErr: function(text) { console.error('[JBIG2]', text); },
    onRuntimeInitialized: function() {
        window.JBIG2Ready = true;
    },
    onAbort: function(what) { console.error('[JBIG2] Aborted:', what); }
};
window.JBIG2Ready = false;
<raw patched jbig2.js source emitted directly>  // runs in global scope, var Module hoists

// 4. Re-initialization function
function initJBIG2Module() {
    window.JBIG2Ready = false;
    window.Module = {
        wasmBinary: window._jbig2WasmBytes,
        noInitialRun: true,
        print: function(text) { console.log('[JBIG2]', text); },
        printErr: function(text) { console.error('[JBIG2]', text); },
        onRuntimeInitialized: function() {
            window.JBIG2Ready = true;
        },
        onAbort: function(what) { console.error('[JBIG2] Aborted:', what); }
    };
    (new Function(window._jbig2LoaderSource))();
}
```

So the loader source appears **twice**: once as executable code (block 3, runs on page load) and once as a `json.dumps`-escaped string (block 2, for re-initialization via `new Function()`). The Module object in both blocks 3 and 4 has 5 properties: `wasmBinary`, `noInitialRun`, `print`, `printErr`, `onRuntimeInitialized`, plus `onAbort`.

### 47.6 Progress Updates During Manual Conversion

`convertPDF()` and `convertZIP()` update `progressText.textContent` directly at each phase:
- "Reading PDF file..." / "Reading ZIP file..."
- "Loading PDF with PDF.js..." / "Parsing ZIP structure..."
- "Rendering page N of M @ DPI DPI..."
- "Processing page N (dithered/sharp)..."
- "Encoding page N with CCITT Group 4..." (G4 path)
- "Prepared page N for JBIG2 encoding..." (JBIG2 path)
- "Initializing JBIG2 encoder..."
- "Encoding N pages with JBIG2..."
- "JBIG2 encoding: <status>"
- "Generating CCITT-compressed PDF (N pages)..." / "Generating JBIG2-compressed PDF (N pages)..."
- "FlateDecode compression: stream N / M..."
- "Creating result ZIP..." (ZIP mode only)

The AI auto-setter's MutationObserver parses these text strings to compute intra-trial progress fractions.

### 47.7 Post-Save State on Tier 1/2

After a tier-1/2 save, the WebView is destroyed and recreated. The user returns to **FILE_LOADED** state (not RESULT). The result PDF data is gone (nulled before `endSave()`). The form settings and input file are restored via `restoreAppState()`, and the user can recompress. The Advanced Tricks section is shown in collapsed/cancelled state (not the result box).

---

## Appendix: Cross-Cutting TODOs

