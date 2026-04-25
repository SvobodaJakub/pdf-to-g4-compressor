#!/usr/bin/env python3
"""
Build script to create single-file HTML application
Combines all JavaScript modules and libraries into one HTML file
Also embeds source code tarball for license compliance
"""

import base64
import os
import subprocess
import tempfile
import shutil

def read_file(path):
    """Read a file and return its contents"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def read_binary(path):
    """Read a binary file"""
    with open(path, 'rb') as f:
        return f.read()

def to_base64(data):
    """Encode string to base64"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')

def read_version():
    """Read VERSION_NAME from ../build-apk.sh"""
    import re
    try:
        with open('../build-apk.sh', 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'^VERSION_NAME="([^"]+)"', line.strip())
                if m:
                    return f'v{m.group(1)}'
    except FileNotFoundError:
        pass
    return ''

def create_source_tarball():
    """Create tar.xz of source code, return base64-encoded content"""
    print("Creating source tarball...")

    # Create temporary file for tarball
    with tempfile.NamedTemporaryFile(suffix='.tar.xz', delete=False) as tmp:
        tarball_path = tmp.name

    try:
        # Create tar.xz with maximum compression
        # Exclude the built HTML file
        # Compress from parent directory to include src/ as top-level
        env = os.environ.copy()
        env['XZ_OPT'] = '-9e'  # Maximum compression for xz

        subprocess.run([
            'tar',
            '-cJf', tarball_path,
            '--exclude=pdf-to-g4-compressor.html',
            '-C', '../..',  # Go to project directory
            'src/'
        ], check=True, capture_output=True, env=env)

        # Read and base64 encode
        with open(tarball_path, 'rb') as f:
            tarball_data = f.read()

        tarball_b64 = base64.b64encode(tarball_data).decode('ascii')

        print(f"  Tarball size: {len(tarball_data):,} bytes")
        print(f"  Base64 size: {len(tarball_b64):,} bytes")

        return tarball_b64

    finally:
        # Clean up temporary file
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)

def create_self_extracting_loader(full_html, pako_code):
    """Create a self-extracting HTML loader that decompresses the full application"""
    import zlib

    print("Creating self-extracting loader...")

    # Compress full HTML with maximum compression
    compressed = zlib.compress(full_html.encode('utf-8'), level=9)
    print(f"  Full HTML size: {len(full_html):,} bytes")
    print(f"  Compressed size: {len(compressed):,} bytes")
    print(f"  Compression ratio: {100 * (1 - len(compressed)/len(full_html)):.1f}%")

    # Base64 encode compressed data
    compressed_b64 = base64.b64encode(compressed).decode('ascii')
    print(f"  Base64 size: {len(compressed_b64):,} bytes")

    # Create minimal loader HTML
    loader_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Monochrome CCITT G4 Compressor - Loading...</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .loader {{
            text-align: center;
            max-width: 400px;
            padding: 40px;
        }}
        .spinner {{
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        h1 {{
            font-size: 24px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        p {{
            font-size: 14px;
            opacity: 0.9;
            line-height: 1.6;
        }}
        .error {{
            background: rgba(255,255,255,0.1);
            border: 2px solid rgba(255,100,100,0.5);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            text-align: left;
        }}
        .error h2 {{
            color: #ffcccc;
            font-size: 18px;
            margin-bottom: 10px;
        }}
        .error pre {{
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="loader" id="loader">
        <div class="spinner"></div>
        <h1>PDF Monochrome CCITT G4 Compressor</h1>
        <p>Decompressing application...</p>
        <p style="font-size: 12px; margin-top: 10px; opacity: 0.7;">This may take a few seconds on slower devices</p>
    </div>

    <!-- Pako library for decompression -->
    <script>
{pako_code}
    </script>

    <!-- Compressed application HTML -->
    <script>
// Self-extracting HTML loader
// The full application is compressed with gzip/deflate and base64-encoded below
const COMPRESSED_HTML_BASE64 = '{compressed_b64}';

(function() {{
    const loaderDiv = document.getElementById('loader');

    try {{
        // Decode base64 to binary
        const compressed = atob(COMPRESSED_HTML_BASE64);
        const bytes = new Uint8Array(compressed.length);
        for (let i = 0; i < compressed.length; i++) {{
            bytes[i] = compressed.charCodeAt(i);
        }}

        // Decompress with pako (gzip/deflate)
        const decompressed = pako.inflate(bytes, {{ to: 'string' }});

        // Save the LOADER HTML (the compressed version) BEFORE clearing document
        // This creates a perfect fixed point: downloaded app = byte-for-byte identical
        // Strip out browser extension pollution (Dark Reader, etc.) for truly pristine output
        const pristineDOM = document.documentElement.cloneNode(true);

        // Remove all injected extension styles/scripts
        pristineDOM.querySelectorAll('.darkreader, [class*="darkreader"]').forEach(el => el.remove());
        pristineDOM.querySelectorAll('style[class*="extension"], script[class*="extension"]').forEach(el => el.remove());

        // Serialize to HTML
        const tempDiv = document.createElement('div');
        tempDiv.appendChild(pristineDOM);
        window.PRISTINE_HTML = '<!DOCTYPE html>\\n' + pristineDOM.outerHTML;

        // Clear existing document content completely
        while (document.head.firstChild) {{
            document.head.removeChild(document.head.firstChild);
        }}
        while (document.body.firstChild) {{
            document.body.removeChild(document.body.firstChild);
        }}

        // Now write the decompressed HTML
        document.open();
        document.write(decompressed);
        document.close();

    }} catch (error) {{
        // Show error if decompression fails
        loaderDiv.innerHTML = `
            <div class="error">
                <h2>Error Loading Application</h2>
                <p>Failed to decompress the application. This may be due to:</p>
                <ul style="margin: 10px 0 10px 20px; text-align: left;">
                    <li>Browser compatibility issue</li>
                    <li>Corrupted file download</li>
                    <li>Insufficient memory</li>
                </ul>
                <p>Please try:</p>
                <ul style="margin: 10px 0 10px 20px; text-align: left;">
                    <li>Refreshing the page</li>
                    <li>Using a different browser (Chrome, Firefox, Edge recommended)</li>
                    <li>Re-downloading the file</li>
                </ul>
                <pre>${{error.message}}</pre>
            </div>
        `;
        console.error('Decompression error:', error);
    }}
}})();
    </script>
</body>
</html>"""

    return loader_html

def main():
    print("Building single-file HTML application...")

    # Read all JavaScript components
    print("Reading JavaScript modules...")
    pako = read_file('libs/pako.min.js')
    pdfjslib = read_file('libs/pdf.legacy.min.js')
    pdfjsworker = read_file('libs/pdf.worker.legacy.min.js')
    pdfjsworker_b64 = to_base64(pdfjsworker)
    i18n_core = read_file('i18n.js')
    i18n_languages = read_file('i18n-languages.js')
    g4enc = read_file('g4enc.js')
    imageprocessing = read_file('imageprocessing.js')
    pdfgen = read_file('pdfgen.js')
    pdfcompress = read_file('pdfcompress.js')
    ziputil = read_file('ziputil.js')
    intro = read_file('intro.js')

    # Read JBIG2 components
    print("Reading JBIG2 modules...")
    jbig2_wasm = read_binary('wasm/jbig2.wasm')
    jbig2_wasm_b64 = to_base64(jbig2_wasm)
    jbig2_js = read_file('wasm/jbig2.js')
    jbig2_wrapper = read_file('jbig2-wrapper.js')
    jbig2pdf_js = read_file('jbig2pdf.js')

    # Read and encode Mongolian font
    print("Reading Mongolian font...")
    with open('NotoSansMongolian-Regular.otf', 'rb') as f:
        mongolian_font = f.read()
    mongolian_font_b64 = to_base64(mongolian_font)

    print(f"  pako: {len(pako):,} bytes")
    print(f"  pdf.js: {len(pdfjslib):,} bytes")
    print(f"  pdf.worker: {len(pdfjsworker):,} bytes")
    print(f"  pdf.worker (base64): {len(pdfjsworker_b64):,} bytes")
    print(f"  Mongolian font: {len(mongolian_font):,} bytes")
    print(f"  Mongolian font (base64): {len(mongolian_font_b64):,} bytes")
    print(f"  jbig2.wasm: {len(jbig2_wasm):,} bytes")
    print(f"  jbig2.wasm (base64): {len(jbig2_wasm_b64):,} bytes")
    print(f"  jbig2.js: {len(jbig2_js):,} bytes")
    print(f"  jbig2-wrapper.js: {len(jbig2_wrapper):,} bytes")
    print(f"  jbig2pdf.js: {len(jbig2pdf_js):,} bytes")

    # Merge i18n files
    print("Merging i18n modules...")
    # i18n_core has TRANSLATIONS = { ... sk: {...}, ... };
    # i18n_languages has const ADDITIONAL_TRANSLATIONS = { hu: {...}, ... };
    # Extract the content between { } from ADDITIONAL_TRANSLATIONS
    import re
    # Find the content of ADDITIONAL_TRANSLATIONS object
    match = re.search(r'const ADDITIONAL_TRANSLATIONS = \{(.*)\};', i18n_languages, re.DOTALL)
    if match:
        additional_langs = match.group(1)
        # Insert additional languages before the closing }; of TRANSLATIONS
        # Note: sk already has trailing comma, so don't add another one
        i18n = i18n_core.replace(
            '    // Continue in next file due to length...\n};',
            additional_langs + '\n};'
        )
    else:
        print("  Warning: Could not parse ADDITIONAL_TRANSLATIONS, using core i18n only")
        i18n = i18n_core
    print(f"  i18n (merged): {len(i18n):,} bytes")

    # Create source tarball
    source_tarball_b64 = create_source_tarball()

    # Read the clean HTML template
    html_template = read_file('template.html')

    # Build the complete JavaScript section
    js_section = f"""
<!-- All JavaScript inlined below -->
<script>
/*
================================================================================
PDF Monochrome CCITT G4 Compressor - Single-File Web Application
================================================================================

Generated by Claude AI
Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

================================================================================
THIRD-PARTY COMPONENTS (All inlined below)
================================================================================

1. PDF.js - Mozilla PDF renderer
   Copyright 2012 Mozilla Foundation
   License: Apache 2.0
   URL: https://github.com/mozilla/pdf.js

2. pako - zlib port to JavaScript
   Copyright (C) 2014-2017 Vitaly Puzrin and Andrei Tuputcyn
   License: MIT
   URL: https://github.com/nodeca/pako

3. G4Enc - CCITT Group 4 Encoder
   Copyright 2020-2022 BitBank Software, Inc. (Larry Bank)
   License: Apache 2.0
   URL: https://github.com/bitbank2/G4ENC
   Note: Ported from C to JavaScript for this project

4. jbig2enc - JBIG2 Encoder (compiled to WASM)
   Copyright (C) 2006 Google Inc.
   License: Apache 2.0
   URL: https://github.com/agl/jbig2enc
   Note: Compiled to WebAssembly with Emscripten

5. Leptonica - Image Processing Library (linked in jbig2enc WASM)
   Copyright © 2001-2020 Leptonica
   License: BSD 2-Clause License
   URL: https://github.com/DanBloomberg/leptonica

6. LibTIFF - TIFFBitRevTable (used in Python source)
   Copyright © 1988-1997 Sam Leffler, © 1991-1997 Silicon Graphics, Inc.
   License: LibTIFF License (BSD-style)
   URL: https://gitlab.com/libtiff/libtiff

================================================================================
PROJECTS STUDIED (NO CODE COPIED)
================================================================================

img2pdf - by Johannes Schauer Marin Rodrigues
Copyright (C) 2012-2021 Johannes Schauer Marin Rodrigues
License: GNU LGPL v3+
URL: https://gitlab.mister-muffin.de/josch/img2pdf

We studied img2pdf to understand CCITT embedding concepts (FillOrder handling,
BlackIs1 parameter, general PDF structure). We did NOT copy any source code.
All implementations are original based on public domain specifications
(TIFF 6.0, PDF 1.4) and permissive licensed sources.

================================================================================
*/

// ============================================================================
// SOURCE CODE TARBALL (Embedded for License Compliance)
// ============================================================================
// The complete source code is embedded below as a base64-encoded tar.xz file.
// To extract: copy base64 text → save to file.txt → base64 -d file.txt > src.tar.xz → tar -xJf src.tar.xz
// This satisfies Apache 2.0 license requirements for source distribution.

const SOURCE_TARBALL_BASE64 = '{source_tarball_b64}';

// ============================================================================
// PAKO (zlib) - MIT License
// ============================================================================
{pako}

// ============================================================================
// Internationalization (i18n)
// Auto-detects browser locale and translates UI
// Supports 40+ languages with regional variants and RTL support
// ============================================================================
{i18n}

// ============================================================================
// PDF.js - Apache 2.0 License
// Mozilla PDF.js v2.16.105 (legacy build for non-module environments)
// ============================================================================
{pdfjslib}

// ============================================================================
// PDF.js Worker Setup
// Decode base64-encoded worker and create Blob URL
// ============================================================================
(function() {{
    // Base64-encoded worker (avoids template literal escaping issues)
    const workerBase64 = '{pdfjsworker_b64}';

    // Decode base64 to binary
    const workerBinary = atob(workerBase64);
    const workerBytes = new Uint8Array(workerBinary.length);
    for (let i = 0; i < workerBinary.length; i++) {{
        workerBytes[i] = workerBinary.charCodeAt(i);
    }}

    // Create Blob URL
    const blob = new Blob([workerBytes], {{ type: 'application/javascript' }});
    const workerUrl = URL.createObjectURL(blob);
    pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;
    console.log('PDF.js worker configured from inline code');
}})();

// ============================================================================
// G4Encoder - Apache 2.0 License
// Ported from https://github.com/bitbank2/G4ENC
// ============================================================================
{g4enc}

// ============================================================================
// JBIG2 Encoder - Apache 2.0 License
// Compiled from https://github.com/agl/jbig2enc (WASM)
// ============================================================================

// JBIG2 WASM Module
(function() {{
    // Base64-encoded WASM binary
    const jbig2WasmBase64 = '{jbig2_wasm_b64}';

    // Decode base64 to binary
    const wasmBinary = atob(jbig2WasmBase64);
    const wasmBytes = new Uint8Array(wasmBinary.length);
    for (let i = 0; i < wasmBinary.length; i++) {{
        wasmBytes[i] = wasmBinary.charCodeAt(i);
    }}

    // Create Module object that jbig2.js will use
    window.Module = {{
        wasmBinary: wasmBytes,
        noInitialRun: true,
        print: function(text) {{
            console.log('[JBIG2]', text);
        }},
        printErr: function(text) {{
            console.error('[JBIG2]', text);
        }},
        onRuntimeInitialized: function() {{
            console.log('[JBIG2] Runtime initialized');
            window.JBIG2Ready = true;
        }},
        onAbort: function(what) {{
            console.error('[JBIG2] Aborted:', what);
        }}
    }};

    window.JBIG2Ready = false;
    console.log('[JBIG2] WASM binary prepared:', wasmBytes.length, 'bytes');
}})();

// JBIG2.js - Emscripten-generated loader
{jbig2_js}

// JBIG2 Wrapper - High-level API
{jbig2_wrapper}

// JBIG2 PDF Generator
{jbig2pdf_js}

// ============================================================================
// Image Processing Pipeline
// ============================================================================
{imageprocessing}

// ============================================================================
// PDF Generation
// ============================================================================
{pdfgen}

// ============================================================================
// PDF Compression
// ============================================================================
{pdfcompress}

// ============================================================================
// ZIP Utilities (minimal reader/writer using pako)
// ============================================================================
{ziputil}

// ============================================================================
// Intro Animation
// Visual tutorial that runs on every load
// ============================================================================
{intro}

// ============================================================================
// Pristine HTML (for self-download feature)
// ============================================================================
// The loader sets window.PRISTINE_HTML with the decompressed full HTML
// before writing it to the document. This pristine copy has no user state,
// no form values, no open modals - just the fresh HTML as built.
// Note: If running directly (not through loader), fall back to current HTML
if (typeof window.PRISTINE_HTML === 'undefined') {{
    window.PRISTINE_HTML = document.documentElement.outerHTML;
}}

// ============================================================================
// STATE MACHINE
// ============================================================================
//
// States: EMPTY → FILE_LOADED → CONVERTING → RESULT / CANCELLED / ERROR_RECOVERY
//
// EMPTY (initial):
//   selectedFile=null, progressBoxState=null
//   Button: disabled ("Choose PDF File")
//
// FILE_LOADED:
//   selectedFile set, totalPageCount known, progressBoxState=null|'cancelled'
//   Button: enabled (unless fileError, pageRangeError, DPI invalid, or RAM limit)
//   Transition: handleFileSelected(file) runs the file-open flow:
//     cleanupPreviousResult → clearFileError → detectFileType → countPages
//     → autoAdjustDPI → updateCompressButton
//
// CONVERTING:
//   conversionInProgress=true, controls disabled
//   Button: clickable (for cancellation only)
//   Transition: convertBtn.click → setFormControlsEnabled(false) → convertPDF/convertZIP
//
// RESULT:
//   progressBoxState='result', window.resultPDF set
//   Shows: size comparison, save button, Advanced Tricks
//   validateFormMatchesResult enables/disables save button
//
// CANCELLED:
//   progressBoxState='cancelled'
//   Shows: Advanced Tricks (collapsed)
//   User cancelled mid-conversion
//
// ERROR_RECOVERY:
//   Unexpected conversion error → recoverFromError()
//   Saves user settings, replays handleFileSelected with same file,
//   restores dither/pageSize/rotation settings → back to FILE_LOADED
//
// Key functions:
//   updateCompressButton() — single source of truth for button, file info,
//     JBIG2 feasibility, RAM override, DPI warning
//   handleFileSelected(file) — file-open flow (used by input, drop, recovery)
//   setFormControlsEnabled(enabled) — enable/disable all form controls
//   defaultResultSettings() — canonical default for resultSettings object
// ============================================================================

// Global variables for state management
var currentLang = 'en';  // Will be set during initialization
var detectedLang = 'en';  // Original detected language
var selectedFile = null;
var isZipMode = false;
var zipProgressPrefix = '';
var resultUsedJBIG2 = false;  // Track whether current result used JBIG2
var totalPageCount = null;  // null = unknown/counting, 0+ = known
var maxPagesPerPDF = null;  // for JBIG2 limit: max pages in any single PDF
var inputFileSize = 0;
var fileError = false;
var pageRangeError = false;

// Track compression settings used to create current result
function defaultResultSettings() {{
    return {{
        fileName: null, ditherMode: null, pageRange: null,
        dpi: null, pageSize: null, useJBIG2: false,
        jbig2Threshold: 0.97, preserveRotation: false,
        includeProducer: true, includeTimestamp: true
    }};
}}
var resultSettings = defaultResultSettings();

// DOM element references (assigned in DOMContentLoaded)
var pdfFileInput, filenameDisplay, fileInfoDiv, convertBtn, progressDiv, progressText;
var uploadArea, pageRangeContainer, pageRangeInput, ditherSelectedRadio;
var dpiStandardRadio, dpiCustomRadio, dpiSliderContainer, dpiSlider, dpiValue, dpiWarning;
var useEnglishCheckbox;

// Conversion cancellation
var conversionInProgress = false;
var cancellationRequested = false;

// Track which box is currently shown so language changes can re-render it
var progressBoxState = null;  // null, 'result', or 'cancelled'

// Detect navigation back from browser cache (bfcache)
// This can leave the app in a weird state - reset state instead of reload
// (reload breaks offline PWA on iOS/Android pull-to-refresh)
window.addEventListener('pageshow', function(event) {{
    if (event.persisted) {{
        console.log('Page loaded from bfcache - resetting state to avoid corruption');
        resetAppState();
    }}
}});

// Reset app to pristine state without network reload
function resetAppState() {{
    // Clear selected file
    selectedFile = null;

    if (pdfFileInput) {{
        pdfFileInput.value = '';
    }}
    if (filenameDisplay) {{
        filenameDisplay.textContent = '';  // Empty, not the button text
    }}

    // Reset all radio buttons to first option
    document.querySelectorAll('input[name="mode"]').forEach((radio, index) => {{
        radio.checked = (index === 0);
    }});
    document.querySelectorAll('input[name="dpiMode"]').forEach((radio, index) => {{
        radio.checked = (index === 0);
    }});
    document.querySelectorAll('input[name="pageSize"]').forEach((radio, index) => {{
        radio.checked = (index === 0);
    }});

    // Reset DPI to 310
    if (dpiValue) {{
        dpiValue.value = '310';
    }}
    if (dpiSlider) {{
        dpiSlider.value = 310;
    }}

    // Clear page range for selective dithering
    if (pageRangeInput) {{
        pageRangeInput.value = '';
        pageRangeInput.disabled = true;
    }}

    // Hide DPI warning
    if (dpiWarning) {{
        dpiWarning.style.display = 'none';
    }}

    // Close modals
    const licenseModal = document.getElementById('licenseModal');
    const aboutModal = document.getElementById('aboutModal');
    const privacyModal = document.getElementById('privacyModal');
    if (licenseModal) {{
        licenseModal.style.display = 'none';
    }}
    if (aboutModal) {{
        aboutModal.style.display = 'none';
    }}
    if (privacyModal) {{
        privacyModal.style.display = 'none';
    }}
    // Notify Android that modals are closed
    if (typeof AndroidModalState !== 'undefined') {{
        AndroidModalState.setModalOpen(false);
    }}

    // Hide GitHub corner
    const githubCorner = document.querySelector('.github-corner');
    if (githubCorner) {{
        githubCorner.style.display = 'none';
    }}

    // Reset conversion state
    conversionInProgress = false;
    cancellationRequested = false;
    progressBoxState = null;

    // Hide progress/result indicator
    if (progressDiv) {{
        progressDiv.style.display = 'none';
        progressDiv.classList.remove('cancelled');
        // Reset progress div styling
        progressDiv.style.background = '#e3f2fd';
        progressDiv.style.borderColor = '';
        progressDiv.style.color = '#1976d2';
        progressDiv.innerHTML = '<span class="spinner"></span><span id="progressText" data-i18n="processing">Processing...</span>';
    }}

    // Clear stored PDF result
    window.resultPDF = null;
    window.resultFilename = null;
    window.originalSize = null;
    window.resultSize = null;
    window.ditherMode = null;
    resultUsedJBIG2 = false;

    // Clear result settings
    resultSettings = defaultResultSettings();

    // Reset file info and errors
    totalPageCount = null;
    maxPagesPerPDF = null;
    inputFileSize = 0;
    fileError = false;
    pageRangeError = false;
    if (fileInfoDiv) fileInfoDiv.textContent = '';
    if (uploadArea) uploadArea.classList.remove('file-error');
    if (pageRangeInput) {{ pageRangeInput.style.borderColor = ''; pageRangeInput.style.background = ''; }}

    // Reset ZIP mode
    isZipMode = false;
    zipProgressPrefix = '';
    if (ditherSelectedRadio) {{
        ditherSelectedRadio.disabled = false;
        var ditherSelectedOption = ditherSelectedRadio.closest('.radio-option');
        if (ditherSelectedOption) ditherSelectedOption.style.opacity = '';
    }}

    // Reset language to detected language (uncheck "Use English")
    if (useEnglishCheckbox) {{
        useEnglishCheckbox.checked = false;
    }}
    currentLang = detectedLang;
    applyTranslations(currentLang);
    if (currentLang !== 'en') {{
        // Ensure correct text direction for RTL languages
        const rtlLanguages = new Set(['ar', 'he', 'ur', 'yi']);
        if (rtlLanguages.has(currentLang)) {{
            document.body.setAttribute('dir', 'rtl');
        }} else {{
            document.body.setAttribute('dir', 'ltr');
        }}
    }}

    // Grey out conversion button (after language reset to use correct translation)
    if (convertBtn) {{
        convertBtn.classList.add('disabled');
        convertBtn.setAttribute('aria-disabled', 'true');
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        convertBtn.textContent = currentT.chooseFile || 'Choose PDF File';
    }}

    console.log('App state reset complete');
}}

// ============================================================================
// Main Application Logic
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {{
    'use strict';

    console.log('PDF Monochrome CCITT G4 Compressor - Initializing...');

    // Initialize internationalization
    detectedLang = detectLanguage(); // User's preferred language (assign to global)
    currentLang = detectedLang;  // Assign to global variable
    console.log('Detected language:', currentLang);
    applyTranslations(currentLang);

    // Apply Mongolian script class if needed
    if (currentLang === 'mn-Mong') {{
        document.body.classList.add('mongolian-script');
    }}

    // Get current translations for dynamic content
    let t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

    // Show "Use English" checkbox if user's preferred language is not English
    const languageSwitch = document.getElementById('languageSwitch');
    useEnglishCheckbox = document.getElementById('useEnglishCheckbox');

    // Mongolian checkbox for regions where traditional Mongolian might be relevant
    const mongolianSwitch = document.getElementById('mongolianSwitch');
    const useMongolianCheckbox = document.getElementById('useMongolianCheckbox');

    // Regions where traditional Mongolian script might be relevant
    // Mongolia + mainland China (Inner Mongolia), but NOT Taiwan, Hong Kong, Macau, Singapore
    const mongolianRelevantRegions = ['mn', 'mn-MN', 'mn-Mong', 'mn-Mong-MN', 'mn-Mong-CN',
                                      'zh-CN', 'zh-Hans', 'zh-Hans-CN'];
    const isMongolianRelevant = mongolianRelevantRegions.some(region =>
        detectedLang === region || detectedLang.startsWith(region + '-'));

    // Always show the checkbox if detected language is not English
    if (detectedLang !== 'en') {{
        languageSwitch.classList.add('show');
    }}

    // Show Mongolian checkbox if in relevant region or if currently using mn-Mong
    if (isMongolianRelevant || currentLang === 'mn-Mong') {{
        mongolianSwitch.classList.add('show');
        if (currentLang === 'mn-Mong') {{
            useMongolianCheckbox.checked = true;
        }}
    }}

    // Handle language switch
    useEnglishCheckbox.addEventListener('change', function() {{
        if (this.checked) {{
            // Switch to English
            currentLang = 'en';
            applyTranslations('en');
            t = TRANSLATIONS.en;
            document.body.setAttribute('dir', 'ltr');
            document.body.classList.remove('mongolian-script');
            updateDPIDisplay(); // Refresh DPI display with new language

            // Uncheck Mongolian checkbox if checked
            if (useMongolianCheckbox.checked) {{
                useMongolianCheckbox.checked = false;
            }}

            // If OS default is English, hide the checkbox (we're back to default state)
            if (detectedLang === 'en') {{
                languageSwitch.classList.remove('show');
                this.checked = false; // Uncheck for clean state
            }}
        }} else {{
            // Switch back to detected language
            currentLang = detectedLang;
            applyTranslations(detectedLang);
            t = TRANSLATIONS[detectedLang] || TRANSLATIONS.en;

            // Handle Mongolian script
            if (detectedLang === 'mn-Mong') {{
                document.body.classList.add('mongolian-script');
                // Check Mongolian checkbox if returning to mn-Mong
                if (useMongolianCheckbox) {{
                    useMongolianCheckbox.checked = true;
                }}
            }} else {{
                document.body.classList.remove('mongolian-script');
            }}

            updateDPIDisplay(); // Refresh DPI display with new language
        }}

        // Re-render the progress box in the new language if visible
        if (progressBoxState === 'result') showResultBox();
        else if (progressBoxState === 'cancelled') showCancelledBox();
    }});

    // Handle Mongolian script switch
    useMongolianCheckbox.addEventListener('change', function() {{
        if (this.checked) {{
            // Switch to traditional Mongolian
            currentLang = 'mn-Mong';
            applyTranslations('mn-Mong');
            t = TRANSLATIONS['mn-Mong'] || TRANSLATIONS.en;
            document.body.setAttribute('dir', 'ltr');
            document.body.classList.add('mongolian-script');
            updateDPIDisplay();

            // Uncheck "Use English" if it was checked
            if (useEnglishCheckbox.checked) {{
                useEnglishCheckbox.checked = false;
            }}

            // Show "Use English" checkbox
            languageSwitch.classList.add('show');
        }} else {{
            // Switch back to detected language
            currentLang = detectedLang;
            applyTranslations(detectedLang);
            t = TRANSLATIONS[detectedLang] || TRANSLATIONS.en;

            // Remove Mongolian script if switching away
            if (detectedLang !== 'mn-Mong') {{
                document.body.classList.remove('mongolian-script');
            }}

            // Handle RTL for detected language
            const rtlLanguages = new Set(['ar', 'he', 'ur', 'yi']);
            if (rtlLanguages.has(detectedLang)) {{
                document.body.setAttribute('dir', 'rtl');
            }} else {{
                document.body.setAttribute('dir', 'ltr');
            }}

            updateDPIDisplay();

            // Hide Mongolian checkbox if OS language is not Mongolian-relevant
            if (!isMongolianRelevant && detectedLang !== 'mn-Mong') {{
                mongolianSwitch.classList.remove('show');
            }}
        }}

        // Re-render the progress box in the new language if visible
        if (progressBoxState === 'result') showResultBox();
        else if (progressBoxState === 'cancelled') showCancelledBox();
    }});

    // selectedFile is now a global variable (declared above)

    // DOM elements (assign to global variables)
    pdfFileInput = document.getElementById('pdfFile');
    filenameDisplay = document.getElementById('filename');
    fileInfoDiv = document.getElementById('fileInfo');
    convertBtn = document.getElementById('convertBtn');
    progressDiv = document.getElementById('progress');
    progressText = document.getElementById('progressText');
    uploadArea = document.getElementById('uploadArea');
    pageRangeContainer = document.getElementById('pageRangeContainer');
    pageRangeInput = document.getElementById('pageRange');
    ditherSelectedRadio = document.getElementById('ditherSelected');
    dpiStandardRadio = document.getElementById('dpiStandard');
    dpiCustomRadio = document.getElementById('dpiCustom');
    dpiSliderContainer = document.getElementById('dpiSliderContainer');
    dpiSlider = document.getElementById('dpiSlider');
    dpiValue = document.getElementById('dpiValue');
    dpiWarning = document.getElementById('dpiWarning');

    console.log('DOM elements loaded:', {{
        pdfFileInput: !!pdfFileInput,
        convertBtn: !!convertBtn,
        uploadArea: !!uploadArea,
        pageRangeContainer: !!pageRangeContainer,
        dpiSlider: !!dpiSlider
    }});

    // DPI slider handler
    function updateDPIDisplay() {{
        const dpi = parseInt(dpiSlider.value);
        dpiValue.value = dpi;
        validateControls();
    }}

    function formatFileSize(bytes) {{
        if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
        if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return bytes + ' B';
    }}

    function getCurrentDPI() {{
        return dpiStandardRadio.checked ? 310 : (parseInt(dpiValue.value) || 310);
    }}

    function getCurrentPageSize() {{
        return document.querySelector('input[name="pageSize"]:checked')?.value || 'a4-portrait';
    }}

    const PAGE_SIZE_INCHES = {{
        'a4-portrait': {{ w: 8.27, h: 11.69 }},
        'a4-landscape': {{ w: 11.69, h: 8.27 }},
        'letter-portrait': {{ w: 8.5, h: 11 }},
        'letter-landscape': {{ w: 11, h: 8.5 }},
        'legal-portrait': {{ w: 8.5, h: 14 }}
    }};

    const RAM_LIMIT = 500 * 1048576;
    const JBIG2_MAX_MPIX = 475;

    function estimateRAMBytes(numPages, dpi, pageSize, useJBIG2, fileSizeBytes) {{
        const dims = PAGE_SIZE_INCHES[pageSize] || PAGE_SIZE_INCHES['a4-portrait'];
        const w = Math.round(dims.w * dpi);
        const h = Math.round(dims.h * dpi);
        const renderPeak = w * h * 16;
        const base = fileSizeBytes * 2 + 150 * 1048576;
        if (useJBIG2) {{
            const bilevelPerPage = Math.ceil(w / 8) * h;
            return base + renderPeak + bilevelPerPage * numPages * 2.5 + numPages * 800000;
        }}
        return base + renderPeak + numPages * 200000;
    }}

    function findMaxSafeDPI(numPages, pageSize, useJBIG2, fileSizeBytes) {{
        let lo = 72, hi = 1200, best = 0;
        while (lo <= hi) {{
            const mid = Math.floor((lo + hi) / 2);
            if (estimateRAMBytes(numPages, mid, pageSize, useJBIG2, fileSizeBytes) <= RAM_LIMIT) {{
                best = mid;
                lo = mid + 1;
            }} else {{
                hi = mid - 1;
            }}
        }}
        return best;
    }}

    function autoAdjustDPI() {{
        if (totalPageCount === null || totalPageCount === 0) return;
        const pageSize = getCurrentPageSize();
        if (estimateRAMBytes(totalPageCount, 310, pageSize, false, inputFileSize) <= RAM_LIMIT) {{
            // This document fits at 310 DPI — restore Standard if it was auto-lowered
            dpiStandardRadio.checked = true;
            dpiSliderContainer.classList.remove('show');
            dpiSlider.value = 310;
            dpiValue.value = 310;
            return;
        }}
        const safeDPI = findMaxSafeDPI(totalPageCount, pageSize, false, inputFileSize);
        if (safeDPI >= 200) {{
            dpiCustomRadio.checked = true;
            dpiSliderContainer.classList.add('show');
            dpiSlider.value = safeDPI;
            dpiValue.value = safeDPI;
        }}
    }}

    function loadPDFWithTimeout(data, timeoutMs) {{
        return new Promise(function(resolve, reject) {{
            const timer = setTimeout(function() {{ reject(new Error('timeout')); }}, timeoutMs);
            pdfjsLib.getDocument({{ data: data }}).promise.then(
                function(pdf) {{ clearTimeout(timer); resolve(pdf); }},
                function(err) {{ clearTimeout(timer); reject(err); }}
            );
        }});
    }}

    async function countPages(file) {{
        const arrayBuffer = await file.arrayBuffer();
        if (isZipMode) {{
            const entries = parseZip(arrayBuffer);
            const pdfEntries = entries.filter(function(e) {{ return e.path.toLowerCase().endsWith('.pdf'); }});
            let total = 0;
            let maxPerPDF = 0;
            let failures = 0;
            for (const entry of pdfEntries) {{
                try {{
                    const pdf = await loadPDFWithTimeout(entry.data, 5000);
                    total += pdf.numPages;
                    if (pdf.numPages > maxPerPDF) maxPerPDF = pdf.numPages;
                    pdf.destroy();
                }} catch (e) {{
                    failures++;
                }}
            }}
            maxPagesPerPDF = maxPerPDF;
            if (failures > 0) throw new Error('Unreadable PDFs in ZIP');
            return total;
        }} else {{
            const pdf = await loadPDFWithTimeout(new Uint8Array(arrayBuffer), 10000);
            const count = pdf.numPages;
            maxPagesPerPDF = count;
            pdf.destroy();
            return count;
        }}
    }}

    // Single source of truth for compress button, file info warnings, and override checkbox.
    // Called on every relevant state change: file select, DPI, page size, JBIG2 toggle, override toggle.
    function updateCompressButton() {{
        if (conversionInProgress) return;
        if (!selectedFile) {{
            if (fileInfoDiv) fileInfoDiv.textContent = '';
            return;
        }}

        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const dpi = getCurrentDPI();
        const pageSize = getCurrentPageSize();
        const n = totalPageCount;
        const known = n !== null;
        const dims = PAGE_SIZE_INCHES[pageSize] || PAGE_SIZE_INCHES['a4-portrait'];

        // ── JBIG2 feasibility (Leptonica 5M symbol limit + 120-page hard cap) ──
        const jbig2Pages    = maxPagesPerPDF || n || 0;
        const jbig2Mpix     = known ? (Math.round(dims.w * dpi) * Math.round(dims.h * dpi) * jbig2Pages) / 1000000 : 0;
        const jbig2TooLarge = known && (jbig2Mpix > JBIG2_MAX_MPIX || jbig2Pages > 120);
        const jbig2Requested = document.getElementById('useJBIG2')?.checked || false;
        const useJBIG2      = jbig2Requested && !jbig2TooLarge;

        // ── Resource state ──────────────────────────────────────────────
        const dpiValid      = !dpiCustomRadio.checked || (!isNaN(dpi) && dpi >= 72 && dpi <= 1200);
        const fileSizeOver  = inputFileSize > RAM_LIMIT;
        const pagesOver     = known && n > 500;
        const ramEst        = estimateRAMBytes(n || 0, dpi, pageSize, useJBIG2, inputFileSize);
        const ramOver       = known && ramEst > RAM_LIMIT;

        // Would default settings (310 DPI, G4) already exceed the limit?
        // True for inherently heavy documents regardless of current DPI.
        const heavyDoc      = known && estimateRAMBytes(n, 310, pageSize, false, inputFileSize) > RAM_LIMIT;

        // Button is blocked when current settings exceed limits (unless overridden)
        const needsOverride = fileSizeOver || pagesOver || ramOver;
        const overrideChecked = document.getElementById('ramOverride')?.checked || false;
        const blocked       = fileError || pageRangeError || !dpiValid || (needsOverride && !overrideChecked);

        // ── 1. Compress button ──────────────────────────────────────────
        if (blocked) {{
            convertBtn.classList.add('disabled');
            convertBtn.setAttribute('aria-disabled', 'true');
        }} else {{
            convertBtn.classList.remove('disabled');
            convertBtn.setAttribute('aria-disabled', 'false');
            convertBtn.textContent = currentT.compressButton || 'Compress';
        }}

        // ── 2. File info (page count + file size) ───────────────────────
        if (fileInfoDiv) {{
            let lines = [];
            if (known) {{
                const p = String(n);
                lines.push((heavyDoc || needsOverride) ? '⚠️ ' + p + ' ⚠️' : p);
            }} else {{
                lines.push('...');
            }}
            const sz = formatFileSize(inputFileSize);
            lines.push(fileSizeOver ? '⚠️ ' + sz + ' ⚠️' : sz);
            fileInfoDiv.innerHTML = lines.join('<br>');
        }}

        // ── 3. Override checkbox in Advanced Tricks ──────────────────────
        const container = document.getElementById('ramOverrideContainer');
        if (container) {{
            if (!dpiValid || !needsOverride) {{
                container.style.display = 'none';
                if (!needsOverride) {{
                    const cb = document.getElementById('ramOverride');
                    if (cb) cb.checked = false;
                }}
            }} else {{
                container.style.display = 'flex';
            }}
        }}

        // ── 4. JBIG2 checkbox feasibility ───────────────────────────────
        const jbig2Cb = document.getElementById('useJBIG2');
        if (jbig2Cb) {{
            const jbig2Warn = jbig2Cb.parentElement.nextElementSibling;
            const jbig2DisabledBox = document.getElementById('jbig2DisabledExplain');
            if (jbig2TooLarge) {{
                jbig2Cb.checked = false;
                jbig2Cb.disabled = true;
                jbig2Cb.parentElement.style.opacity = '0.4';
                if (jbig2Warn) jbig2Warn.style.opacity = '0.4';
                const opts = document.getElementById('jbig2ThresholdOptions');
                if (opts) opts.style.display = 'none';
                if (jbig2DisabledBox) {{
                    const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
                    if (jbig2Pages > 120) {{
                        const msg = currentT.jbig2DisabledPages || 'JBIG2 is disabled: this PDF has {{pages}} pages, exceeding the 120-page limit.';
                        jbig2DisabledBox.textContent = msg.replace('{{pages}}', String(jbig2Pages));
                    }} else {{
                        const msg = currentT.jbig2DisabledMpix || 'JBIG2 is disabled: total image data ({{mpix}} megapixels) exceeds the 475 megapixel limit.';
                        jbig2DisabledBox.textContent = msg.replace('{{mpix}}', String(Math.round(jbig2Mpix))).replace('{{pages}}', String(jbig2Pages));
                    }}
                    jbig2DisabledBox.style.display = 'block';
                }}
            }} else {{
                jbig2Cb.disabled = false;
                jbig2Cb.parentElement.style.opacity = '';
                if (jbig2Warn) jbig2Warn.style.opacity = '';
                if (jbig2DisabledBox) jbig2DisabledBox.style.display = 'none';
            }}
        }}

        // ── 5. Override risk acceptance text ─────────────────────────────
        const overrideCb = document.getElementById('ramOverride');
        const overrideLabel = overrideCb ? container.querySelector('label') : null;
        if (overrideLabel && needsOverride) {{
            const nukeSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36"><circle cx="16" cy="33" r="4" fill="#b0b0b0"/><circle cx="20" cy="33" r="4" fill="#a8a8a8"/><circle cx="18" cy="31" r="4.5" fill="#c0c0c0"/><circle cx="15" cy="29" r="3.5" fill="#b8b8b8"/><circle cx="21" cy="29" r="3.5" fill="#b0b0b0"/><circle cx="18" cy="27" r="4" fill="#c8c8c8"/><circle cx="16" cy="25" r="3.5" fill="#bfbfbf"/><circle cx="20" cy="25" r="3.5" fill="#c0c0c0"/><ellipse cx="18" cy="23" rx="14" ry="4" fill="#e8720a"/><ellipse cx="18" cy="23" rx="10" ry="3" fill="#f5a623"/><circle cx="7" cy="18" r="8" fill="#e8720a"/><circle cx="29" cy="18" r="8" fill="#e8720a"/><circle cx="18" cy="19" r="9" fill="#f5a623"/><circle cx="11" cy="13" r="7" fill="#c0392b"/><circle cx="25" cy="13" r="7" fill="#c0392b"/><circle cx="18" cy="14" r="8" fill="#d44030"/><circle cx="14" cy="8" r="5.5" fill="#808080"/><circle cx="22" cy="8" r="5.5" fill="#808080"/><circle cx="18" cy="9" r="6" fill="#909090"/><circle cx="18" cy="5" r="4" fill="#a0a0a0"/><circle cx="18" cy="3" r="2.5" fill="#b0b0b0"/></svg>';
            let labelHtml = formatFileSize(ramEst) + ' RAM 🔥💻⚡️⚠️ 💥 🐕☕🔥 ¯\\\\_(ツ)_/¯ <img src="data:image/svg+xml;base64,' + btoa(nukeSvg) + '" style="height:1.2em;vertical-align:-0.15em" alt=""><span style="font-size:0">🍄</span>😎';
            if (overrideCb.checked) {{
                const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
                const riskText = currentT.ramOverrideAcceptRisk || ' (my device can run out of memory or run hot, the application might crash, and I accept that risk, just let me click the Compress button)';
                labelHtml += '<span style="font-style: italic; opacity: 0.8;">' + riskText + '</span>';
            }}
            overrideLabel.innerHTML = labelHtml;
        }}

        // ── 6. DPI warning (depends on RAM estimate) ────────────────────
        updateDPIWarning();
    }}

    function validateControls() {{
        updateCompressButton();
    }}

    function updateDPIWarning() {{
        const dpi = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value);
        const ditherEnabled = document.querySelector('input[name="mode"]:checked').value !== 'nodither';

        dpiWarning.classList.remove('show', 'low-quality', 'high-filesize', 'high-compute');
        dpiWarning.textContent = '';

        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const n = totalPageCount;
        const known = n !== null && n > 0;

        // RAM-based warnings (when page count is known)
        if (known && selectedFile) {{
            const useJBIG2 = document.getElementById('useJBIG2')?.checked || false;
            const pageSize = getCurrentPageSize();
            const est = estimateRAMBytes(n, dpi, pageSize, useJBIG2, inputFileSize);
            const ramStr = formatFileSize(est);

            if (est > RAM_LIMIT) {{
                dpiWarning.classList.add('show', 'high-compute');
                const msg = currentT.ramWarningCritical || 'Warning: Very high estimated resource usage ({{ram}}).';
                dpiWarning.textContent = msg.replace('{{ram}}', ramStr);
                return;
            }} else if (est > 400 * 1048576) {{
                dpiWarning.classList.add('show', 'high-filesize');
                const msg = currentT.ramWarningHigh || 'Note: High estimated resource usage ({{ram}}).';
                dpiWarning.textContent = msg.replace('{{ram}}', ramStr);
                return;
            }}
        }}

        // DPI-only warnings (when page count unknown or RAM is fine)
        if ((!ditherEnabled && dpi < 200) || (ditherEnabled && dpi < 240)) {{
            dpiWarning.classList.add('show', 'low-quality');
            dpiWarning.textContent = currentT.lowQualityWarning || 'Warning: Low DPI may result in poor quality output.';
        }}
    }}

    // Sync slider when user types in DPI input
    dpiValue.addEventListener('input', function() {{
        // Filter out non-digit characters
        let cleaned = this.value.replace(/[^0-9]/g, '');
        if (cleaned !== this.value) {{
            this.value = cleaned;
        }}

        let val = parseInt(this.value);
        if (!isNaN(val)) {{
            // Update slider position (clamped to slider bounds)
            if (val < 72) {{
                dpiSlider.value = 72;
            }} else if (val > 1200) {{
                dpiSlider.value = 1200;
            }} else {{
                dpiSlider.value = val;
            }}
        }}

        // Validate controls to disable/enable convert button
        validateControls();
        validateFormMatchesResult();
    }});

    dpiSlider.addEventListener('input', function() {{
        updateDPIDisplay();
        validateFormMatchesResult();
    }});
    updateDPIDisplay(); // Initialize display

    // Show/hide DPI slider based on radio selection
    document.querySelectorAll('input[name="dpiMode"]').forEach(radio => {{
        radio.addEventListener('change', function() {{
            if (this.value === 'custom') {{
                dpiSliderContainer.classList.add('show');
            }} else {{
                dpiSliderContainer.classList.remove('show');
            }}
            validateControls();
            validateFormMatchesResult();
        }});
    }});

    // Show/hide page range input based on radio selection
    document.querySelectorAll('input[name="mode"]').forEach(radio => {{
        radio.addEventListener('change', function() {{
            if (this.value === 'dither-selected') {{
                pageRangeContainer.classList.add('show');
            }} else {{
                pageRangeContainer.classList.remove('show');
            }}
            updateDPIWarning(); // Update warning when dithering mode changes
            validateFormMatchesResult();
        }});
    }});

    // Validate when page range changes
    pageRangeInput.addEventListener('input', function() {{
        const val = this.value.trim();
        if (val && ditherSelectedRadio.checked) {{
            try {{
                parsePageRange(val, totalPageCount);
                clearPageRangeError();
            }} catch (e) {{
                setPageRangeError();
            }}
        }} else {{
            clearPageRangeError();
        }}
        validateFormMatchesResult();
    }});

    // Validate when page size changes
    document.querySelectorAll('input[name="pageSize"]').forEach(radio => {{
        radio.addEventListener('change', function() {{
            updateCompressButton();
            validateFormMatchesResult();
        }});
    }});

    function setFormControlsEnabled(enabled) {{
        pdfFileInput.disabled = !enabled;
        dpiSlider.disabled = !enabled;
        pageRangeInput.disabled = !enabled;
        document.querySelectorAll('input[name="mode"]').forEach(radio => {{
            radio.disabled = !enabled;
        }});
        document.querySelectorAll('input[name="dpiMode"]').forEach(radio => {{
            radio.disabled = !enabled;
        }});
        document.querySelectorAll('input[name="pageSize"]').forEach(radio => {{
            radio.disabled = !enabled;
        }});
        if (enabled && isZipMode) updateZipModeUI();
    }}

    function cleanupPreviousResult() {{
        // Free large result data
        window.resultPDF = null;
        window.resultFilename = null;
        window.originalSize = null;
        window.resultSize = null;
        window.ditherMode = null;
        resultUsedJBIG2 = false;
        conversionInProgress = false;
        cancellationRequested = false;
        resultSettings = defaultResultSettings();
        const hadAdvancedTricks = progressBoxState !== null;
        progressBoxState = null;
        if (progressDiv) {{
            progressDiv.classList.remove('cancelled');
            progressDiv.style.background = '';
            progressDiv.style.borderColor = '';
            progressDiv.style.color = '';
            if (hadAdvancedTricks) {{
                progressBoxState = 'cancelled';
                progressDiv.classList.add('cancelled');
                progressDiv.innerHTML = '<div style="margin-top: 0;">' + buildAdvancedTricksHTML(false) + '</div>';
                progressDiv.style.display = 'block';
                attachAdvancedTricksListeners(false);
            }} else {{
                progressDiv.style.display = 'none';
                progressDiv.innerHTML = '';
            }}
        }}
        // Free canvas backing stores
        var previewCanvas = document.getElementById('previewCanvas');
        if (previewCanvas) {{
            previewCanvas.width = 0;
            previewCanvas.height = 0;
        }}
    }}

    async function recoverFromError() {{
        // Read form settings (these survive since they're in the main form, not the progress box)
        const savedFile = selectedFile;
        const savedDitherMode = document.querySelector('input[name="mode"]:checked')?.value || 'nodither';
        const savedPageRange = (savedDitherMode === 'dither-selected' && pageRangeInput.value.trim()) ? pageRangeInput.value.trim() : null;
        const savedPageSize = document.querySelector('input[name="pageSize"]:checked')?.value || 'a4-portrait';

        // Read Advanced Tricks settings from resultSettings (saved before conversion started,
        // since the DOM checkboxes were destroyed when the progress spinner replaced them)
        const savedPreserveRotation = resultSettings.preserveRotation;
        const savedIncludeProducer = resultSettings.includeProducer;
        const savedIncludeTimestamp = resultSettings.includeTimestamp;

        // Validate page range — only keep it if it was valid
        let pageRangeValid = false;
        if (savedPageRange) {{
            try {{
                parsePageRange(savedPageRange, totalPageCount);
                pageRangeValid = true;
            }} catch (e) {{ /* invalid, don't restore */ }}
        }}

        // Full reset and re-open the same file
        clearPageRangeError();
        if (savedFile) {{
            await handleFileSelected(savedFile);
            if (fileError) return;
        }}

        // Restore page size
        const pageSizeRadio = document.querySelector('input[name="pageSize"][value="' + savedPageSize + '"]');
        if (pageSizeRadio) pageSizeRadio.checked = true;

        // Restore dither mode and page range
        if (savedDitherMode && !isZipMode) {{
            const ditherRadio = document.getElementById(
                savedDitherMode === 'dither' ? 'dither' :
                savedDitherMode === 'dither-selected' ? 'ditherSelected' : 'noDither'
            );
            if (ditherRadio && !ditherRadio.disabled) {{
                ditherRadio.checked = true;
                if (savedDitherMode === 'dither-selected') {{
                    pageRangeContainer.classList.add('show');
                    if (pageRangeValid && savedPageRange) {{
                        pageRangeInput.value = savedPageRange;
                    }}
                }}
            }}
        }}

        // Restore Advanced Tricks settings (expand if any non-default)
        const needsExpand = savedPreserveRotation || !savedIncludeProducer || !savedIncludeTimestamp;
        const cb = document.getElementById('preserveRotation');
        if (cb) cb.checked = savedPreserveRotation;
        const prodCb = document.getElementById('includeProducer');
        if (prodCb) prodCb.checked = savedIncludeProducer;
        const tsCb = document.getElementById('includeTimestamp');
        if (tsCb) tsCb.checked = savedIncludeTimestamp;

        if (needsExpand) {{
            const content = document.getElementById('advancedTricksContent');
            const toggle = document.getElementById('advancedTricksToggle');
            if (content) content.style.display = 'block';
            if (toggle) {{
                const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
                toggle.textContent = '▼ ' + (currentT.advancedTricks || 'Advanced technological tricks');
            }}
        }}

        updateCompressButton();
    }}

    function setFileError() {{
        fileError = true;
        uploadArea.classList.add('file-error');
        updateCompressButton();
    }}

    function clearFileError() {{
        fileError = false;
        uploadArea.classList.remove('file-error');
    }}

    function setPageRangeError() {{
        pageRangeError = true;
        pageRangeInput.style.borderColor = '#c0392b';
        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        pageRangeInput.style.background = isDark ? '#3a2020' : '#fdf0ef';
        updateCompressButton();
    }}

    function clearPageRangeError() {{
        if (!pageRangeError) return;
        pageRangeError = false;
        pageRangeInput.style.borderColor = '';
        pageRangeInput.style.background = '';
        updateCompressButton();
    }}

    // Detect file type by magic bytes and update ZIP mode state
    async function detectFileType(file) {{
        var header = new Uint8Array(await file.slice(0, 4).arrayBuffer());
        if (header[0] === 0x50 && header[1] === 0x4B && header[2] === 0x03 && header[3] === 0x04) {{
            isZipMode = true;
        }} else {{
            isZipMode = false;
        }}
        updateZipModeUI();
    }}

    // Update UI state based on ZIP mode
    function updateZipModeUI() {{
        if (isZipMode) {{
            // Disable dither-selected radio (no sense in selective dithering with multiple files)
            ditherSelectedRadio.disabled = true;
            var ditherSelectedOption = ditherSelectedRadio.closest('.radio-option');
            if (ditherSelectedOption) ditherSelectedOption.style.opacity = '0.5';

            // If dither-selected was checked, switch to noDither
            if (ditherSelectedRadio.checked) {{
                var noDitherRadio = document.getElementById('noDither');
                if (noDitherRadio) noDitherRadio.checked = true;
            }}

            // Hide page range container
            pageRangeContainer.classList.remove('show');
        }} else {{
            // Re-enable dither-selected radio
            ditherSelectedRadio.disabled = false;
            var ditherSelectedOption = ditherSelectedRadio.closest('.radio-option');
            if (ditherSelectedOption) ditherSelectedOption.style.opacity = '';
        }}
    }}

    async function handleFileSelected(file) {{
        selectedFile = file;
        cleanupPreviousResult();
        clearFileError();
        inputFileSize = file.size;
        totalPageCount = null;
        maxPagesPerPDF = null;
        await detectFileType(file);
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        filenameDisplay.textContent = file.name;
        convertBtn.textContent = currentT.compressButton || 'Compress';
        updateCompressButton();
        try {{
            totalPageCount = await countPages(file);
        }} catch (e) {{
            totalPageCount = 0;
        }}
        if (totalPageCount <= 0) {{
            setFileError();
            return;
        }}
        autoAdjustDPI();
        updateCompressButton();
    }}

    // File upload handling
    pdfFileInput.addEventListener('change', async function(e) {{
        if (e.target.files[0]) await handleFileSelected(e.target.files[0]);
    }});

    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {{
        e.preventDefault();
        uploadArea.classList.add('dragover');
    }});

    uploadArea.addEventListener('dragleave', function() {{
        uploadArea.classList.remove('dragover');
    }});

    uploadArea.addEventListener('drop', async function(e) {{
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (conversionInProgress) return;
        if (e.dataTransfer.files.length > 0) await handleFileSelected(e.dataTransfer.files[0]);
    }});

    // Convert button - keyboard activation for role="button" div
    convertBtn.addEventListener('keydown', function(e) {{
        if (e.key === 'Enter' || e.key === ' ') {{
            e.preventDefault();
            convertBtn.click();
        }}
    }});
    convertBtn.addEventListener('click', async function() {{
        if (!selectedFile) return;

        // If conversion is in progress, cancel it
        if (conversionInProgress) {{
            cancellationRequested = true;
            return;
        }}

        if (convertBtn.classList.contains('disabled')) return;

        // Read checkbox states BEFORE destroying the result box
        const useJBIG2Checkbox = document.getElementById('useJBIG2');
        const useJBIG2ForThisRun = useJBIG2Checkbox ? useJBIG2Checkbox.checked : false;
        const jbig2ThresholdRadio = document.querySelector('input[name="jbig2Threshold"]:checked');
        const jbig2ThresholdForThisRun = jbig2ThresholdRadio ? parseFloat(jbig2ThresholdRadio.value) : 0.97;
        const preserveRotationCheckbox = document.getElementById('preserveRotation');
        const preserveRotationForThisRun = preserveRotationCheckbox ? preserveRotationCheckbox.checked : false;
        const includeProducerCheckbox = document.getElementById('includeProducer');
        const includeProducerForThisRun = includeProducerCheckbox ? includeProducerCheckbox.checked : true;
        const includeTimestampCheckbox = document.getElementById('includeTimestamp');
        const includeTimestampForThisRun = includeTimestampCheckbox ? includeTimestampCheckbox.checked : true;

        const ditherMode = document.querySelector('input[name="mode"]:checked').value;
        let ditherConfig = null;

        if (ditherMode === 'dither') {{
            ditherConfig = {{ mode: 'all' }};
        }} else if (ditherMode === 'dither-selected') {{
            const pageRangeStr = pageRangeInput.value.trim();
            if (!pageRangeStr) {{
                setPageRangeError();
                return;
            }}
            try {{
                const pages = parsePageRange(pageRangeStr, totalPageCount);
                ditherConfig = {{ mode: 'selected', pages: pages }};
            }} catch (error) {{
                setPageRangeError();
                return;
            }}
        }} else {{
            ditherConfig = {{ mode: 'none' }};
        }}

        // Save Advanced Tricks settings into resultSettings so that
        // showCancelledBox/buildAdvancedTricksHTML can restore them
        resultSettings.preserveRotation = preserveRotationForThisRun;
        resultSettings.includeProducer = includeProducerForThisRun;
        resultSettings.includeTimestamp = includeTimestampForThisRun;
        resultSettings.useJBIG2 = useJBIG2ForThisRun;
        resultSettings.jbig2Threshold = jbig2ThresholdForThisRun;

        conversionInProgress = true;
        cancellationRequested = false;
        let errorRecoveryNeeded = false;

        try {{
            // Reset progress box to show processing state (in case result box was displayed)
            progressDiv.classList.remove('cancelled');
            progressDiv.innerHTML = '<span class="spinner"></span><span id="progressText" data-i18n="processing">Processing...</span>';
            progressDiv.style.background = '#e3f2fd';
            progressDiv.style.borderColor = '';
            progressDiv.style.color = '#1976d2';
            progressDiv.style.display = 'block';

            // Update the global progressText reference since we just recreated the element
            progressText = document.getElementById('progressText');
            progressText.textContent = 'Loading PDF...';

            // Disable all controls during conversion (except convert button for cancellation)
            setFormControlsEnabled(false);

            // Get selected DPI (use 310 if standard mode is selected)
            const targetDPI = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value);

            // Get selected page size
            const pageSize = document.querySelector('input[name="pageSize"]:checked').value;

            // Process the file (PDF or ZIP)
            const metadataOpts = {{ includeProducer: includeProducerForThisRun, includeTimestamp: includeTimestampForThisRun }};
            if (isZipMode) {{
                await convertZIP(selectedFile, ditherConfig, targetDPI, pageSize, useJBIG2ForThisRun, jbig2ThresholdForThisRun, preserveRotationForThisRun, metadataOpts);
            }} else {{
                await convertPDF(selectedFile, ditherConfig, targetDPI, pageSize, useJBIG2ForThisRun, jbig2ThresholdForThisRun, preserveRotationForThisRun, metadataOpts);
            }}

        }} catch (error) {{
            if (error.message === 'CONVERSION_CANCELLED') {{
                showCancelledBox();
            }} else {{
                console.error('Conversion error:', error);
                errorRecoveryNeeded = true;
            }}
        }} finally {{
            conversionInProgress = false;
            cancellationRequested = false;
            setFormControlsEnabled(true);
            if (errorRecoveryNeeded) {{
                await recoverFromError();
            }}
            updateCompressButton();
        }}
    }});

    // Parse page range string (e.g., "1, 3-5, 8, 10-12")
    function parsePageRange(rangeStr, maxPage) {{
        const pages = new Set();
        const parts = rangeStr.split(',').map(s => s.trim()).filter(s => s);

        for (const part of parts) {{
            if (/^\\d+\\s*-\\s*\\d+$/.test(part)) {{
                const [start, end] = part.split('-').map(s => parseInt(s.trim(), 10));
                if (start < 1 || end < start) throw new Error('Invalid range');
                if (maxPage && end > maxPage) throw new Error('Page out of range');
                for (let i = start; i <= end; i++) {{
                    if (pages.has(i)) throw new Error('Duplicate page');
                    pages.add(i);
                }}
            }} else if (/^\\d+$/.test(part)) {{
                const page = parseInt(part, 10);
                if (page < 1) throw new Error('Invalid page');
                if (maxPage && page > maxPage) throw new Error('Page out of range');
                if (pages.has(page)) throw new Error('Duplicate page');
                pages.add(page);
            }} else {{
                throw new Error('Invalid input');
            }}
        }}

        if (pages.size === 0) {{
            throw new Error('No valid pages');
        }}

        return pages;
    }}

    // Main conversion function
    async function convertPDF(file, ditherConfig, targetDPI, pageSize, useJBIG2, jbig2Threshold, preserveRotation, metadataOpts) {{
        progressText.textContent = 'Reading PDF file...';

        // Read file as ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        const pdfData = new Uint8Array(arrayBuffer);
        const originalSize = pdfData.length;

        progressText.textContent = 'Loading PDF with PDF.js...';
        console.log('Loading PDF, size:', pdfData.length, 'bytes');

        let finalPDF;

        if (useJBIG2) {{
            // JBIG2 encoding path: init encoder BEFORE rendering so pages
            // are written as PBMs incrementally (no bilevel accumulation in JS)
            progressText.textContent = 'Initializing JBIG2 encoder...';
            await new Promise(r => setTimeout(r, 0));

            const encoder = new JBIG2Encoder();
            await encoder.init();
            encoder.prepareEncoding();

            // Render pages — each page's bilevel data is written to WASM FS
            // and immediately discarded from JS. Only metadata is kept.
            const pages = await renderPDFPages(pdfData, ditherConfig, targetDPI, pageSize, useJBIG2, preserveRotation, encoder);

            if (!pages || pages.length === 0) {{
                throw new Error('No pages rendered from PDF');
            }}

            progressText.textContent = `Encoding ${{pages.length}} pages with JBIG2...`;
            await new Promise(r => setTimeout(r, 0));

            const jbig2Result = await encoder.encode({{
                lossy: true,
                threshold: jbig2Threshold,
                symbolCoding: true,
                progressCallback: (current, total, status) => {{
                    progressText.textContent = `JBIG2 encoding: ${{status}}`;
                }}
            }});

            progressText.textContent = `Generating JBIG2-compressed PDF (${{pages.length}} pages)...`;
            await new Promise(r => setTimeout(r, 0));

            const jbig2Pages = pages.map((p, i) => ({{
                width: p.width,
                height: p.height,
                data: jbig2Result.pages[i],
                rotate: p.rotate || 0
            }}));

            const jbig2PDF = createJBIG2PDF({{
                globalData: jbig2Result.sym,
                pages: jbig2Pages,
                metadataOptions: metadataOpts
            }});

            finalPDF = await compressPDF(jbig2PDF, pako, (current, total) => {{
                progressText.textContent = `FlateDecode compression: stream ${{current}} / ${{total}}...`;
            }});
        }} else {{
            // CCITT G4 path: each page is G4-compressed inline during rendering
            const pages = await renderPDFPages(pdfData, ditherConfig, targetDPI, pageSize, useJBIG2, preserveRotation);

            if (!pages || pages.length === 0) {{
                throw new Error('No pages rendered from PDF');
            }}

            progressText.textContent = `Generating CCITT-compressed PDF (${{pages.length}} pages)...`;
            await new Promise(r => setTimeout(r, 0));
            const compressedPDF = createPDF(pages, metadataOpts);

            finalPDF = await compressPDF(compressedPDF, pako, (current, total) => {{
                progressText.textContent = `FlateDecode compression: stream ${{current}} / ${{total}}...`;
            }});
        }}

        // Store result for later download
        window.resultPDF = finalPDF;
        window.resultFilename = file.name.replace('.pdf', useJBIG2 ? '_jbig2.pdf' : '_ccittG4.pdf');
        window.originalSize = originalSize;
        window.resultSize = finalPDF.length;
        window.ditherMode = ditherConfig.mode;
        resultUsedJBIG2 = useJBIG2;  // Track which method was used

        // Save all compression settings for validation
        resultSettings.fileName = file.name;
        resultSettings.ditherMode = ditherConfig.mode;
        resultSettings.pageRange = ditherConfig.mode === 'selected' ? [...(ditherConfig.pages || [])].join(',') : null;
        resultSettings.dpi = targetDPI;
        resultSettings.pageSize = pageSize;
        resultSettings.useJBIG2 = useJBIG2;
        resultSettings.jbig2Threshold = jbig2Threshold;
        resultSettings.preserveRotation = preserveRotation;
        resultSettings.includeProducer = metadataOpts.includeProducer;
        resultSettings.includeTimestamp = metadataOpts.includeTimestamp;

        // Show result box instead of downloading
        showResultBox();
    }}

    // Batch conversion for ZIP files containing PDFs
    async function convertZIP(file, ditherConfig, targetDPI, pageSize, useJBIG2, jbig2Threshold, preserveRotation, metadataOpts) {{
        progressText.textContent = 'Reading ZIP file...';

        // Read ZIP into ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();

        progressText.textContent = 'Parsing ZIP structure...';
        const allEntries = parseZip(arrayBuffer);

        // Filter for PDF files (case-insensitive)
        const pdfEntries = allEntries.filter(function(e) {{
            return e.path.toLowerCase().endsWith('.pdf');
        }});
        if (pdfEntries.length === 0) {{
            throw new Error('No PDF files found in ZIP');
        }}

        // Initialize JBIG2 encoder if needed (once for all files)
        let jbig2Encoder = null;
        if (useJBIG2) {{
            progressText.textContent = 'Initializing JBIG2 encoder...';
            jbig2Encoder = new JBIG2Encoder();
            await jbig2Encoder.init();
        }}

        var totalOriginalSize = 0;
        var resultEntries = [];

        for (var i = 0; i < pdfEntries.length; i++) {{
            if (cancellationRequested) throw new Error('CONVERSION_CANCELLED');

            var entry = pdfEntries[i];
            var fileLabel = 'File ' + (i + 1) + '/' + pdfEntries.length;
            totalOriginalSize += entry.data.length;

            // Set progress prefix for renderPDFPages
            zipProgressPrefix = fileLabel + ': ';

            var finalPDF;

            if (useJBIG2) {{
                // JBIG2: prepare encoder, render pages writing PBMs incrementally
                jbig2Encoder.prepareEncoding();

                progressText.textContent = fileLabel + ': Loading PDF...';
                var pages = await renderPDFPages(entry.data, ditherConfig, targetDPI, pageSize, useJBIG2, preserveRotation, jbig2Encoder);

                if (!pages || pages.length === 0) {{
                    console.warn('No pages rendered from ' + entry.path + ', skipping');
                    continue;
                }}

                progressText.textContent = fileLabel + `: Encoding ${{pages.length}} pages with JBIG2...`;
                await new Promise(r => setTimeout(r, 0));

                const jbig2Result = await jbig2Encoder.encode({{
                    lossy: true,
                    threshold: jbig2Threshold,
                    symbolCoding: true,
                    progressCallback: (current, total, status) => {{
                        progressText.textContent = fileLabel + ': ' + status;
                    }}
                }});

                progressText.textContent = fileLabel + `: Generating JBIG2-compressed PDF (${{pages.length}} pages)...`;
                await new Promise(r => setTimeout(r, 0));

                const jbig2Pages = pages.map((p, idx) => ({{
                    width: p.width,
                    height: p.height,
                    data: jbig2Result.pages[idx],
                    rotate: p.rotate || 0
                }}));

                const jbig2PDF = createJBIG2PDF({{
                    globalData: jbig2Result.sym,
                    pages: jbig2Pages,
                    metadataOptions: metadataOpts
                }});

                finalPDF = await compressPDF(jbig2PDF, pako, (current, total) => {{
                    progressText.textContent = fileLabel + `: FlateDecode compression: stream ${{current}} / ${{total}}...`;
                }});
            }} else {{
                // CCITT G4 path
                progressText.textContent = fileLabel + ': Loading PDF...';
                var pages = await renderPDFPages(entry.data, ditherConfig, targetDPI, pageSize, useJBIG2, preserveRotation);

                if (!pages || pages.length === 0) {{
                    console.warn('No pages rendered from ' + entry.path + ', skipping');
                    continue;
                }}

                progressText.textContent = fileLabel + `: Generating CCITT-compressed PDF (${{pages.length}} pages)...`;
                await new Promise(r => setTimeout(r, 0));
                var compressedPDF = createPDF(pages, metadataOpts);

                finalPDF = await compressPDF(compressedPDF, pako, (current, total) => {{
                    progressText.textContent = fileLabel + `: FlateDecode compression: stream ${{current}} / ${{total}}...`;
                }});
            }}

            resultEntries.push({{ path: entry.path, data: finalPDF }});
        }}

        // Clear progress prefix
        zipProgressPrefix = '';

        if (resultEntries.length === 0) {{
            throw new Error('No PDFs could be processed from the ZIP');
        }}

        progressText.textContent = 'Creating result ZIP...';
        var resultZip = createZip(resultEntries);

        // Store results (same globals as convertPDF)
        window.resultPDF = resultZip;
        window.resultFilename = file.name.replace(/\\.zip$/i, useJBIG2 ? '_jbig2.zip' : '_ccittG4.zip');
        window.originalSize = totalOriginalSize;
        window.resultSize = resultZip.length;
        window.ditherMode = ditherConfig.mode;
        resultUsedJBIG2 = useJBIG2;  // Track which method was used

        // Save all compression settings for validation
        resultSettings.fileName = file.name;
        resultSettings.ditherMode = ditherConfig.mode;
        resultSettings.pageRange = ditherConfig.mode === 'selected' ? [...(ditherConfig.pages || [])].join(',') : null;
        resultSettings.dpi = targetDPI;
        resultSettings.pageSize = pageSize;
        resultSettings.useJBIG2 = useJBIG2;
        resultSettings.jbig2Threshold = jbig2Threshold;
        resultSettings.preserveRotation = preserveRotation;
        resultSettings.includeProducer = metadataOpts.includeProducer;
        resultSettings.includeTimestamp = metadataOpts.includeTimestamp;

        showResultBox();
    }}

    // Show result box with compression results
    // Build the Advanced Tricks HTML section (shared between result and cancelled states)
    function buildAdvancedTricksHTML(expanded) {{
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const advancedTricksText = currentT.advancedTricks || 'Advanced technological tricks';
        const display = expanded ? 'block' : 'none';
        const arrow = expanded ? '▼' : '▶';
        const jbig2Checked = resultSettings.useJBIG2;

        return `
                <a href="javascript:void(0)" id="advancedTricksToggle" class="advanced-toggle" style="display: inline-block; color: #667eea; cursor: pointer; font-weight: 500; text-decoration: none; margin-bottom: 10px;">${{arrow}} ${{advancedTricksText}}</a>
                <div id="advancedTricksContent" class="advanced-content" style="display: ${{display}}; margin-top: 10px; padding: 15px; background: white; border-radius: 4px; border: 1px solid #ddd;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <input type="checkbox" id="useJBIG2" name="useJBIG2" ${{jbig2Checked ? 'checked' : ''}} style="width: 18px; height: 18px; cursor: pointer;">
                        <label for="useJBIG2" style="cursor: pointer; color: #333; font-weight: 500;">${{currentT.useJBIG2Label || 'Use lossy JBIG2 compression instead of CCITT G4'}}</label>
                    </div>
                    <div style="font-size: 13px; color: #856404; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; line-height: 1.5;">${{currentT.jbig2Warning || '⚠️ Improve compression by using JBIG2 compression instead of CCITT G4 compression. Small similar characters might be confused (e.g. 6 with 8). Old devices might be unable to open the PDF.'}}</div>
                    <div id="jbig2DisabledExplain" style="display: none; font-size: 13px; color: #856404; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; line-height: 1.5; margin-top: 8px;"></div>

                    <div id="jbig2ThresholdOptions" style="display: ${{jbig2Checked ? 'block' : 'none'}}; margin-top: 12px; padding: 12px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e0e0e0;">
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="radio" id="jbig2Threshold097" name="jbig2Threshold" value="0.97" ${{resultSettings.jbig2Threshold === 0.97 ? 'checked' : ''}} style="width: 16px; height: 16px; cursor: pointer;">
                                <label for="jbig2Threshold097" style="cursor: pointer; color: #333; font-family: 'Courier New', monospace;">jbig2enc -t 0.97</label>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="radio" id="jbig2Threshold092" name="jbig2Threshold" value="0.92" ${{resultSettings.jbig2Threshold === 0.92 ? 'checked' : ''}} style="width: 16px; height: 16px; cursor: pointer;">
                                <label for="jbig2Threshold092" style="cursor: pointer; color: #333; font-family: 'Courier New', monospace;">⚠️ jbig2enc -t 0.92</label>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="radio" id="jbig2Threshold085" name="jbig2Threshold" value="0.85" ${{resultSettings.jbig2Threshold === 0.85 ? 'checked' : ''}} style="width: 16px; height: 16px; cursor: pointer;">
                                <label for="jbig2Threshold085" style="cursor: pointer; color: #333; font-family: 'Courier New', monospace;">⚠️⚠️ jbig2enc -t 0.85</label>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 14px;">
                        <input type="checkbox" id="preserveRotation" name="preserveRotation" ${{resultSettings.preserveRotation ? 'checked' : ''}} style="width: 18px; height: 18px; cursor: pointer;">
                        <label for="preserveRotation" style="cursor: pointer; color: #333; font-weight: 500;">${{currentT.preserveRotationLabel || 'Try to preserve page rotation'}}</label>
                    </div>

                    <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid #eee;">
                        <div style="font-weight: 500; color: #333; margin-bottom: 10px;">${{currentT.metadataSection || 'Metadata'}}</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <input type="checkbox" id="includeProducer" name="includeProducer" ${{resultSettings.includeProducer ? 'checked' : ''}} style="width: 18px; height: 18px; cursor: pointer;">
                            <label for="includeProducer" style="cursor: pointer; color: #333;">PDF Monochrome G4 Compressor</label>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <input type="checkbox" id="includeTimestamp" name="includeTimestamp" ${{resultSettings.includeTimestamp ? 'checked' : ''}} style="width: 18px; height: 18px; cursor: pointer;">
                            <label for="includeTimestamp" style="cursor: pointer; color: #333;">${{currentT.includeTimestampLabel || 'Include Created & Modified timestamps'}}</label>
                        </div>
                    </div>
                    <div id="ramOverrideContainer" style="display: none; align-items: center; gap: 8px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #eee;">
                        <input type="checkbox" id="ramOverride" style="width: 18px; height: 18px; cursor: pointer;">
                        <label for="ramOverride" style="cursor: pointer; color: #333; font-weight: 500;"></label>
                    </div>
                </div>`;
    }}

    // Attach event listeners for the Advanced Tricks section controls
    function attachAdvancedTricksListeners(withValidation) {{
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const advancedTricksText = currentT.advancedTricks || 'Advanced technological tricks';

        // Toggle handler
        var advancedTricksToggle = document.getElementById('advancedTricksToggle');
        var advancedTricksContent = document.getElementById('advancedTricksContent');
        if (advancedTricksToggle && advancedTricksContent) {{
            advancedTricksToggle.addEventListener('click', function(e) {{
                e.preventDefault();
                const isShown = advancedTricksContent.style.display === 'block';
                if (!isShown) {{
                    advancedTricksContent.style.display = 'block';
                    advancedTricksToggle.textContent = '▼ ' + advancedTricksText;
                }} else {{
                    advancedTricksContent.style.display = 'none';
                    advancedTricksToggle.textContent = '▶ ' + advancedTricksText;
                }}
            }});
        }}

        // JBIG2 checkbox: show/hide threshold options + recalculate RAM estimate
        var useJBIG2Checkbox = document.getElementById('useJBIG2');
        if (useJBIG2Checkbox) {{
            useJBIG2Checkbox.addEventListener('change', function() {{
                var thresholdOptions = document.getElementById('jbig2ThresholdOptions');
                if (thresholdOptions) {{
                    thresholdOptions.style.display = this.checked ? 'block' : 'none';
                }}
                updateCompressButton();
                if (withValidation) validateFormMatchesResult();
            }});
        }}

        // RAM override checkbox
        var ramOverrideCb = document.getElementById('ramOverride');
        if (ramOverrideCb) {{
            ramOverrideCb.addEventListener('change', updateCompressButton);
        }}

        updateCompressButton();

        if (withValidation) {{
            var preserveRotationCb = document.getElementById('preserveRotation');
            if (preserveRotationCb) {{
                preserveRotationCb.addEventListener('change', validateFormMatchesResult);
            }}
            var includeProducerCb = document.getElementById('includeProducer');
            if (includeProducerCb) {{
                includeProducerCb.addEventListener('change', validateFormMatchesResult);
            }}
            var includeTimestampCb = document.getElementById('includeTimestamp');
            if (includeTimestampCb) {{
                includeTimestampCb.addEventListener('change', validateFormMatchesResult);
            }}
            var thresholdRadios = document.querySelectorAll('input[name="jbig2Threshold"]');
            thresholdRadios.forEach(function(radio) {{
                radio.addEventListener('change', validateFormMatchesResult);
            }});
        }}
    }}

    function showCancelledBox() {{
        progressBoxState = 'cancelled';
        progressDiv.style.background = '';
        progressDiv.style.borderColor = '';
        progressDiv.style.color = '';
        progressDiv.classList.add('cancelled');

        progressDiv.innerHTML = '<div style="margin-top: 0;">' + buildAdvancedTricksHTML(false) + '</div>';
        progressDiv.style.display = 'block';

        attachAdvancedTricksListeners(false);
    }}

    function showResultBox() {{
        progressBoxState = 'result';
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const originalSize = window.originalSize;
        const resultSize = window.resultSize;
        const ratio = resultSize / originalSize;

        // Format sizes
        const formatSize = (bytes) => {{
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' kiB';
            return (bytes / (1024 * 1024)).toFixed(2) + ' MiB';
        }};

        // Build the message (handle RTL languages)
        const rtlLanguages = new Set(['ar', 'he', 'ur', 'yi']);
        const isRTL = rtlLanguages.has(currentLang);

        // For both LTR and RTL: keep the same logical order (old → new)
        // But for RTL, explicitly mark the size comparison as LTR text
        // so numbers and units display correctly left-to-right
        let message;
        if (isRTL) {{
            message = '<span dir="ltr">' + formatSize(originalSize) + ' → ' + formatSize(resultSize) + '</span>';
        }} else {{
            message = formatSize(originalSize) + ' → ' + formatSize(resultSize);
        }}

        // Clear cancelled state if present
        progressDiv.classList.remove('cancelled');

        // Determine compression result and set box color accordingly
        if (ratio < 0.6) {{
            // Success (green)
            progressDiv.style.background = '#d4edda';
            progressDiv.style.borderColor = '#c3e6cb';
            progressDiv.style.color = '#155724';
        }} else if (ratio <= 1.0) {{
            // Bad compression (yellow)
            progressDiv.style.background = '#fff3cd';
            progressDiv.style.borderColor = '#ffeaa7';
            progressDiv.style.color = '#856404';
        }} else {{
            // Got bigger (orange)
            progressDiv.style.background = '#ffe5cc';
            progressDiv.style.borderColor = '#ffb366';
            progressDiv.style.color = '#8B4513';
        }}

        const isSuccess = ratio < 0.6;

        // Add additional messages if not successful
        if (!isSuccess) {{
            message += '<br><br>';
            message += currentT.resultRecommendIgnore;

            if (ratio >= 0.6 && ratio <= 1.0) {{
                message += currentT.resultDidntCompressWell;
            }} else if (ratio > 1.0) {{
                message += currentT.resultBecameBigger;
            }}

            message += '<br><br>' + currentT.resultAppPurpose;

            if (window.ditherMode === 'all') {{
                message += '<br><br>' + currentT.resultDitheringNote;
                message += currentT.resultDitheringAdvice;
            }} else if (window.ditherMode === 'selected') {{
                message += '<br><br>' + currentT.resultDitheringNote;
            }}
        }}

        // Build HTML with advanced tricks and save button (always shown)
        const advancedTricksExpanded = resultSettings.useJBIG2 || resultSettings.preserveRotation || !resultSettings.includeProducer || !resultSettings.includeTimestamp;
        let resultHTML = `
            <div style="font-weight: bold; margin-bottom: 15px;">${{message}}</div>
            <div style="margin-top: 20px;">
                ${{buildAdvancedTricksHTML(advancedTricksExpanded)}}
            </div>
            <div id="saveResultBtn" class="action-btn" role="button" tabindex="0" style="width: auto; padding: 10px 20px; background: #667eea; border-radius: 4px; margin-top: 20px;">${{currentT.resultSaveButton}}</div>
        `;

        progressDiv.innerHTML = resultHTML;
        progressDiv.style.display = 'block';

        // Attach save button handler
        var saveBtn = document.getElementById('saveResultBtn');
        saveBtn.addEventListener('click', function() {{
            if (this.classList.contains('disabled')) return;
            downloadFile(window.resultPDF, window.resultFilename);
        }});
        saveBtn.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter' || e.key === ' ') {{
                e.preventDefault();
                if (!this.classList.contains('disabled')) {{
                    downloadFile(window.resultPDF, window.resultFilename);
                }}
            }}
        }});

        attachAdvancedTricksListeners(true);
        validateFormMatchesResult();
    }}

    // Validate that current form settings match the compressed result
    function validateFormMatchesResult() {{
        const saveBtn = document.getElementById('saveResultBtn');
        if (!saveBtn) return;  // Save button doesn't exist (no result shown)
        if (!resultSettings.fileName) return;  // No result to compare against

        // Make sure all required elements exist
        if (!selectedFile || !dpiStandardRadio || !dpiSlider) return;

        // Check all form settings against saved result settings
        const currentFileName = selectedFile.name;
        const currentDitherMode = document.querySelector('input[name="mode"]:checked')?.value || 'no-dither';
        const currentPageRange = currentDitherMode === 'dither-selected' ? (pageRangeInput?.value || '').trim() : null;
        const currentDPI = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value) || 310;
        const currentPageSize = document.querySelector('input[name="pageSize"]:checked')?.value || 'a4-portrait';
        const currentUseJBIG2 = document.getElementById('useJBIG2')?.checked || false;
        const currentJBIG2Threshold = parseFloat(document.querySelector('input[name="jbig2Threshold"]:checked')?.value || '0.97');
        const currentPreserveRotation = document.getElementById('preserveRotation')?.checked || false;
        const currentIncludeProducer = document.getElementById('includeProducer')?.checked ?? true;
        const currentIncludeTimestamp = document.getElementById('includeTimestamp')?.checked ?? true;

        // Convert radio button values to the ditherConfig.mode values used during compression
        let compareDitherMode = 'none';
        if (currentDitherMode === 'no-dither') compareDitherMode = 'none';
        else if (currentDitherMode === 'dither') compareDitherMode = 'all';
        else if (currentDitherMode === 'dither-selected') compareDitherMode = 'selected';

        // Build normalized page range for comparison
        let normalizedCurrentPageRange = null;
        if (compareDitherMode === 'selected' && currentPageRange) {{
            try {{
                const pages = parsePageRange(currentPageRange);
                normalizedCurrentPageRange = [...pages].join(',');
            }} catch (e) {{
                // Invalid page range - doesn't match
                normalizedCurrentPageRange = 'INVALID';
            }}
        }}

        const settingsMatch = (
            currentFileName === resultSettings.fileName &&
            compareDitherMode === resultSettings.ditherMode &&
            normalizedCurrentPageRange === resultSettings.pageRange &&
            currentDPI === resultSettings.dpi &&
            currentPageSize === resultSettings.pageSize &&
            currentUseJBIG2 === resultSettings.useJBIG2 &&
            currentJBIG2Threshold === resultSettings.jbig2Threshold &&
            currentPreserveRotation === resultSettings.preserveRotation &&
            currentIncludeProducer === resultSettings.includeProducer &&
            currentIncludeTimestamp === resultSettings.includeTimestamp
        );

        if (settingsMatch) {{
            // Settings match - enable save button
            saveBtn.classList.remove('disabled');
            saveBtn.style.opacity = '1';
            saveBtn.style.cursor = 'pointer';
        }} else {{
            // Settings don't match - grey out save button
            saveBtn.classList.add('disabled');
            saveBtn.style.opacity = '0.5';
            saveBtn.style.cursor = 'not-allowed';
        }}
    }}

    // Render PDF pages using PDF.js
    async function renderPDFPages(pdfData, ditherConfig, targetDPI, pageSize, useJBIG2, preserveRotation, jbig2Encoder) {{
        // Load PDF document
        const loadingTask = pdfjsLib.getDocument({{ data: pdfData }});
        const pdf = await loadingTask.promise;

        console.log('PDF loaded, pages:', pdf.numPages);

        // Validate selected pages if in selected mode
        if (ditherConfig.mode === 'selected') {{
            const maxPage = Math.max(...ditherConfig.pages);
            if (maxPage > pdf.numPages) {{
                throw new Error(`Page ${{maxPage}} does not exist (PDF has ${{pdf.numPages}} pages)`);
            }}
        }}

        // Define page sizes in inches (width × height)
        const PAGE_SIZES = {{
            'a4-portrait': {{ width: 8.27, height: 11.69 }},
            'a4-landscape': {{ width: 11.69, height: 8.27 }},
            'letter-portrait': {{ width: 8.5, height: 11 }},
            'letter-landscape': {{ width: 11, height: 8.5 }},
            'legal-portrait': {{ width: 8.5, height: 14 }}
        }};

        // Get selected page dimensions
        const pageDimensions = PAGE_SIZES[pageSize] || PAGE_SIZES['a4-portrait'];

        // Calculate page dimensions at target DPI
        const PAGE_WIDTH_PX = Math.round(pageDimensions.width * targetDPI);
        const PAGE_HEIGHT_PX = Math.round(pageDimensions.height * targetDPI);

        // For backward compatibility, keep A4 variables pointing to current page size
        const A4_WIDTH_PX = PAGE_WIDTH_PX;
        const A4_HEIGHT_PX = PAGE_HEIGHT_PX;

        const pages = [];

        // Get canvas and context for rendering
        const previewCanvas = document.getElementById('previewCanvas');
        const previewDiv = document.getElementById('debugPreview');
        const previewInfo = document.getElementById('previewInfo');

        // Debug preview disabled - uncomment to show preview during processing
        // previewDiv.style.display = 'block';

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
            if (cancellationRequested) throw new Error('CONVERSION_CANCELLED');

            progressText.textContent = zipProgressPrefix + `Rendering page ${{pageNum}} of ${{pdf.numPages}} @ ${{targetDPI}} DPI...`;

            const page = await pdf.getPage(pageNum);

            // Calculate scale to fit page on destination canvas
            // Note: getViewport() without rotation uses the page's inherent rotation.
            // Passing rotation: N would OVERRIDE the page's rotation, which we must avoid
            // unless the user explicitly enabled rotation preservation.
            const viewport72 = page.getViewport({{ scale: 1.0 }});

            // Detect if adding 90° rotation would improve coverage on the destination page
            let additionalRotation = null;
            if (preserveRotation) {{
                const scaleNormal = Math.min(A4_WIDTH_PX / viewport72.width, A4_HEIGHT_PX / viewport72.height);
                const rotatedViewport = page.getViewport({{ scale: 1.0, rotation: (page.rotate + 90) % 360 }});
                const scaleRotated = Math.min(A4_WIDTH_PX / rotatedViewport.width, A4_HEIGHT_PX / rotatedViewport.height);
                if (scaleRotated > scaleNormal) {{
                    additionalRotation = (page.rotate + 90) % 360;
                }}
            }}

            const viewportForScale = additionalRotation !== null
                ? page.getViewport({{ scale: 1.0, rotation: additionalRotation }})
                : viewport72;
            const scaleX = A4_WIDTH_PX / viewportForScale.width;
            const scaleY = A4_HEIGHT_PX / viewportForScale.height;
            const scale = Math.min(scaleX, scaleY);

            const scaledViewport = additionalRotation !== null
                ? page.getViewport({{ scale: scale, rotation: additionalRotation }})
                : page.getViewport({{ scale: scale }});

            // Create temporary canvas for isolated rendering
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = Math.floor(scaledViewport.width);
            tempCanvas.height = Math.floor(scaledViewport.height);
            const tempContext = tempCanvas.getContext('2d');

            // Fill temp canvas with white background first
            tempContext.fillStyle = 'white';
            tempContext.fillRect(0, 0, tempCanvas.width, tempCanvas.height);

            // Render PDF page to temporary canvas (isolated from A4 canvas transforms)
            await page.render({{
                canvasContext: tempContext,
                viewport: scaledViewport
            }}).promise;

            if (cancellationRequested) throw new Error('CONVERSION_CANCELLED');

            // Now composite onto A4 canvas
            previewCanvas.width = A4_WIDTH_PX;
            previewCanvas.height = A4_HEIGHT_PX;
            const context = previewCanvas.getContext('2d');

            // Fill with white background
            context.fillStyle = 'white';
            context.fillRect(0, 0, A4_WIDTH_PX, A4_HEIGHT_PX);

            // Center the rendered page on the A4 canvas
            const offsetX = Math.floor((A4_WIDTH_PX - tempCanvas.width) / 2);
            const offsetY = Math.floor((A4_HEIGHT_PX - tempCanvas.height) / 2);

            // Composite temporary canvas onto A4 canvas
            context.drawImage(tempCanvas, offsetX, offsetY);

            // Free temp canvas backing store immediately
            tempCanvas.width = 0;
            tempCanvas.height = 0;

            console.log(`Page ${{pageNum}} rendered: ${{Math.floor(scaledViewport.width)}}x${{Math.floor(scaledViewport.height)}} centered on ${{A4_WIDTH_PX}}x${{A4_HEIGHT_PX}} canvas`);

            // Get image data from canvas
            const imageData = context.getImageData(0, 0, previewCanvas.width, previewCanvas.height);

            // Determine if this page should be dithered
            let shouldDither = false;
            if (ditherConfig.mode === 'all') {{
                shouldDither = true;
            }} else if (ditherConfig.mode === 'selected') {{
                shouldDither = ditherConfig.pages.has(pageNum);
            }}
            // else mode === 'none', shouldDither stays false

            progressText.textContent = zipProgressPrefix + `Processing page ${{pageNum}} (${{shouldDither ? 'dithered' : 'sharp'}})...`;

            // Process through image pipeline
            const processed = processImage(imageData, {{ dither: shouldDither }});

            const bytesPerRow = Math.ceil(processed.width / 8);
            console.log(`Page ${{pageNum}} bilevel: ${{processed.width}}x${{processed.height}}, bytesPerRow: ${{bytesPerRow}}`);

            if (useJBIG2) {{
                // JBIG2 path: write bilevel PBM to WASM FS immediately, don't accumulate in JS
                progressText.textContent = zipProgressPrefix + `Prepared page ${{pageNum}} for JBIG2 encoding...`;

                jbig2Encoder.addPage(processed.width, processed.height, processed.data);

                pages.push({{
                    width: processed.width,
                    height: processed.height,
                    pageWidthPt: Math.round(pageDimensions.width * 72),
                    pageHeightPt: Math.round(pageDimensions.height * 72),
                    rotate: additionalRotation !== null ? 270 : 0
                }});
            }} else {{
                // G4 path: encode with CCITT Group 4
                progressText.textContent = zipProgressPrefix + `Encoding page ${{pageNum}} with CCITT Group 4...`;

                // Encode with G4
                const encoder = new G4Encoder();
                encoder.init(processed.width, processed.height, G4ENC_MSB_FIRST);

                // G4 encoder expects bit=1 for WHITE, but our bilevel has bit=1 for BLACK
                // Invert in-place (processed.data is not used after this)
                for (let i = 0; i < processed.data.length; i++) {{
                    processed.data[i] = ~processed.data[i] & 0xFF;
                }}

                for (let y = 0; y < processed.height; y++) {{
                    const rowStart = y * bytesPerRow;
                    const rowData = processed.data.subarray(rowStart, rowStart + bytesPerRow);
                    const result = encoder.addLine(rowData);

                    if (result === G4ENC_IMAGE_COMPLETE) {{
                        console.log(`G4 encoding complete at line ${{y + 1}}`);
                        break;
                    }}
                }}

                const compressedData = encoder.getData();
                const compressionRatio = (compressedData.length / (bytesPerRow * processed.height) * 100);

                console.log(`Page ${{pageNum}} G4 compressed: ${{compressedData.length}} bytes (ratio: ${{compressionRatio.toFixed(1)}}%)`);

                console.log(`Page ${{pageNum}} G4 stream: ${{compressedData.length}} bytes, first 20 bytes:`, Array.from(compressedData.slice(0, 20)).map(b => '0x' + b.toString(16).padStart(2, '0')).join(' '));

                pages.push({{
                    width: processed.width,
                    height: processed.height,
                    data: compressedData,
                    pageWidthPt: Math.round(pageDimensions.width * 72),   // Convert inches to points (1 inch = 72 points)
                    pageHeightPt: Math.round(pageDimensions.height * 72),
                    rotate: additionalRotation !== null ? 270 : 0
                }});
            }}

            page.cleanup();
        }}

        pdf.cleanup();
        return pages;
    }}

    // Download helper
    function downloadFile(data, filename) {{
        // Detect MIME type from filename
        var mimeType = filename.toLowerCase().endsWith('.zip') ? 'application/zip' : 'application/pdf';

        // Check if running in Android WebView with file handler
        if (typeof AndroidFileHandler !== 'undefined') {{
            // Convert data to base64
            let base64Data;
            if (data instanceof Uint8Array) {{
                // Convert Uint8Array to base64
                let binary = '';
                for (let i = 0; i < data.length; i++) {{
                    binary += String.fromCharCode(data[i]);
                }}
                base64Data = btoa(binary);
            }} else {{
                base64Data = btoa(data);
            }}

            // Use Android file handler
            AndroidFileHandler.saveFile(filename, base64Data, mimeType);
        }} else {{
            // Standard browser download
            const blob = new Blob([data], {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    }}

    // Service Worker registration (for PWA)
    if ('serviceWorker' in navigator) {{
        window.addEventListener('load', function() {{
            // Service worker registration would go here
            // For single-file app, we skip this for now
        }});
    }}

    // License modal functionality
    const licenseModal = document.getElementById('licenseModal');
    const showLicenseBtn = document.getElementById('showLicense');
    const closeLicenseBtn = document.getElementById('closeLicense');

    if (showLicenseBtn) {{
        showLicenseBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            licenseModal.classList.add('show');
            // Notify Android that a modal is open (for back button handling)
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(true);
            }}
        }});
    }}

    if (closeLicenseBtn) {{
        closeLicenseBtn.addEventListener('click', function() {{
            licenseModal.classList.remove('show');
            // Notify Android that modal is closed
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }});
    }}

    // Close modal when clicking outside
    licenseModal.addEventListener('click', function(e) {{
        if (e.target === licenseModal) {{
            licenseModal.classList.remove('show');
        }}
    }});

    // About modal functionality
    const aboutModal = document.getElementById('aboutModal');
    const showAboutBtn = document.getElementById('showAbout');
    const closeAboutBtn = document.getElementById('closeAbout');

    if (showAboutBtn) {{
        showAboutBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            aboutModal.classList.add('show');
            // Notify Android that a modal is open (for back button handling)
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(true);
            }}
        }});
    }}

    if (closeAboutBtn) {{
        closeAboutBtn.addEventListener('click', function() {{
            aboutModal.classList.remove('show');
            // Notify Android that modal is closed
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }});
    }}

    // Close about modal when clicking outside
    aboutModal.addEventListener('click', function(e) {{
        if (e.target === aboutModal) {{
            aboutModal.classList.remove('show');
        }}
    }});

    // Privacy Policy modal functionality
    const privacyModal = document.getElementById('privacyModal');
    const showPrivacyBtn = document.getElementById('showPrivacy');
    const closePrivacyBtn = document.getElementById('closePrivacy');

    if (showPrivacyBtn) {{
        showPrivacyBtn.addEventListener('click', function(e) {{
            e.preventDefault();
            privacyModal.classList.add('show');
            // Notify Android that a modal is open (for back button handling)
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(true);
            }}
        }});
    }}

    if (closePrivacyBtn) {{
        closePrivacyBtn.addEventListener('click', function() {{
            privacyModal.classList.remove('show');
            // Notify Android that modal is closed
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }});
    }}

    // Close privacy modal when clicking outside
    privacyModal.addEventListener('click', function(e) {{
        if (e.target === privacyModal) {{
            privacyModal.classList.remove('show');
            // Notify Android that modal is closed
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }}
    }});

    // Privacy Policy toggle in About modal
    const privacyToggle = document.getElementById('privacyToggle');
    const privacyContent = document.getElementById('privacyContent');

    if (privacyToggle) {{
        privacyToggle.addEventListener('click', function(e) {{
            e.preventDefault();
            const isShown = privacyContent.classList.contains('show');

            if (!isShown) {{
                privacyContent.classList.add('show');
                privacyToggle.textContent = '▼ View Privacy Policy';
            }} else {{
                privacyContent.classList.remove('show');
                privacyToggle.textContent = '▶ View Privacy Policy';
            }}
        }});
    }}

    // Language selector modal functionality
    const LANGUAGE_NAMES = {{
        'af': 'Afrikaans', 'am': 'አማርኛ', 'ar': 'العربية', 'as': 'অসমীয়া', 'az': 'Azərbaycan',
        'be': 'Беларуская', 'bg': 'Български', 'bn': 'বাংলা', 'bo': 'བོད་ཡིག', 'bs': 'Bosanski',
        'ca': 'Català', 'cs': 'Čeština', 'da': 'Dansk', 'de': 'Deutsch', 'el': 'Ελληνικά',
        'en': 'English', 'es': 'Español', 'et': 'Eesti', 'eu': 'Euskara', 'fa': 'فارسی',
        'fi': 'Suomi', 'fr': 'Français', 'gl': 'Galego', 'gu': 'ગુજરાતી', 'he': 'עברית',
        'hi': 'हिन्दी', 'hr': 'Hrvatski', 'hu': 'Magyar', 'hy': 'Հայերեն', 'id': 'Indonesia',
        'is': 'Íslenska', 'it': 'Italiano', 'ja': '日本語', 'jv': 'Jawa', 'ka': 'ქართული',
        'kk': 'Қазақ', 'km': 'ខ្មែរ', 'kn': 'ಕನ್ನಡ', 'ko': '한국어', 'ky': 'Кыргызча',
        'lo': 'ລາວ', 'lt': 'Lietuvių', 'lv': 'Latviešu', 'mk': 'Македонски', 'ml': 'മലയാളം',
        'mn': 'Монгол', 'mn-Mong': 'ᠮᠣᠩᠭᠣᠯ', 'mr': 'मराठी', 'ms': 'Melayu', 'my': 'မြန်မာ', 'nb': 'Norsk (Bokmål)',
        'ne': 'नेपाली', 'nl': 'Nederlands', 'nn': 'Norsk (Nynorsk)', 'or': 'ଓଡ଼ିଆ', 'pa': 'ਪੰਜਾਬੀ',
        'pl': 'Polski', 'pt': 'Português', 'ro': 'Română', 'ru': 'Русский', 'si': 'සිංහල',
        'sk': 'Slovenčina', 'sl': 'Slovenščina', 'sq': 'Shqip', 'sr-Cyrl': 'Српски', 'sr-Latn': 'Srpski',
        'sv': 'Svenska', 'sw': 'Kiswahili',
        'ta': 'தமிழ்', 'te': 'తెలుగు', 'tg': 'Тоҷикӣ', 'th': 'ไทย', 'tk': 'Türkmen',
        'tl': 'Tagalog', 'tr': 'Türkçe', 'tt': 'Татар', 'uk': 'Українська', 'ur': 'اردو',
        'uz': 'Oʻzbek', 'vi': 'Tiếng Việt', 'yi': 'ייִדיש', 'zh-Hans': '简体中文', 'zh-Hant': '繁體中文',
        'zu': 'isiZulu'
    }};

    const languageModal = document.getElementById('languageModal');
    const languageSelectorBtn = document.getElementById('languageSelectorBtn');
    const closeLanguageModal = document.getElementById('closeLanguageModal');
    const languageList = document.getElementById('languageList');

    // Populate language list
    function populateLanguageList() {{
        languageList.innerHTML = '';

        // Get all available languages and sort by code
        const allLanguages = Object.keys(TRANSLATIONS).sort();

        allLanguages.forEach(code => {{
            const item = document.createElement('div');
            item.className = 'language-item';
            if (code === currentLang) {{
                item.classList.add('active');
            }}
            // Make Mongolian script display vertically in the selector
            if (code === 'mn-Mong') {{
                item.classList.add('mongolian-vertical');
            }}

            const nativeName = LANGUAGE_NAMES[code] || code.toUpperCase();
            item.innerHTML = `<span class="language-code">${{code}}</span>${{nativeName}}`;

            item.addEventListener('click', function() {{
                // Switch language
                currentLang = code;
                applyTranslations(code);

                // Handle "Use English" checkbox visibility and state
                const languageSwitch = document.getElementById('languageSwitch');
                if (code !== 'en') {{
                    // Show and uncheck "Use English" checkbox for non-English languages
                    if (languageSwitch) {{
                        languageSwitch.classList.add('show');
                    }}
                    if (useEnglishCheckbox) {{
                        useEnglishCheckbox.checked = false;
                    }}
                }} else {{
                    // Hide checkbox when English is selected
                    if (languageSwitch) {{
                        languageSwitch.classList.remove('show');
                    }}
                }}

                // Update RTL if needed
                const rtlLanguages = new Set(['ar', 'he', 'ur', 'yi']);
                if (rtlLanguages.has(code)) {{
                    document.body.setAttribute('dir', 'rtl');
                    document.body.classList.remove('mongolian-script');
                }} else if (code === 'mn-Mong') {{
                    // Traditional Mongolian script - vertical writing
                    document.body.setAttribute('dir', 'ltr');
                    document.body.classList.add('mongolian-script');
                }} else {{
                    document.body.setAttribute('dir', 'ltr');
                    document.body.classList.remove('mongolian-script');
                }}

                // Handle "Use Mongolian" checkbox visibility and state
                const mongolianSwitch = document.getElementById('mongolianSwitch');
                const useMongolianCheckbox = document.getElementById('useMongolianCheckbox');
                if (code === 'mn-Mong') {{
                    // Show and check Mongolian checkbox when mn-Mong is selected
                    if (mongolianSwitch) {{
                        mongolianSwitch.classList.add('show');
                    }}
                    if (useMongolianCheckbox) {{
                        useMongolianCheckbox.checked = true;
                    }}
                }} else {{
                    // Uncheck Mongolian checkbox when other language is selected
                    if (useMongolianCheckbox) {{
                        useMongolianCheckbox.checked = false;
                    }}
                    // Keep showing if in Mongolian-relevant region
                    // Mongolia + mainland China (Inner Mongolia), NOT Taiwan/HK/Macau/Singapore
                    const mongolianRelevantRegions = ['mn', 'mn-MN', 'mn-Mong', 'mn-Mong-MN', 'mn-Mong-CN',
                                                      'zh', 'zh-CN', 'zh-Hans', 'zh-Hans-CN'];
                    const isMongolianRelevant = mongolianRelevantRegions.some(region =>
                        detectedLang === region || detectedLang.startsWith(region + '-'));
                    if (!isMongolianRelevant && mongolianSwitch) {{
                        mongolianSwitch.classList.remove('show');
                    }}
                }}

                // Refresh DPI warning in new language
                updateDPIWarning();

                // Re-render the progress box in the new language if visible
                if (progressBoxState === 'result') showResultBox();
                else if (progressBoxState === 'cancelled') showCancelledBox();

                // Close all modals
                const aboutModal = document.getElementById('aboutModal');
                const licenseModal = document.getElementById('licenseModal');
                const privacyModal = document.getElementById('privacyModal');
                if (aboutModal) {{
                    aboutModal.classList.remove('show');
                }}
                if (licenseModal) {{
                    licenseModal.classList.remove('show');
                }}
                if (privacyModal) {{
                    privacyModal.classList.remove('show');
                }}
                languageModal.classList.remove('show');
                if (typeof AndroidModalState !== 'undefined') {{
                    AndroidModalState.setModalOpen(false);
                }}
            }});

            languageList.appendChild(item);
        }});
    }}

    if (languageSelectorBtn) {{
        languageSelectorBtn.addEventListener('click', function() {{
            populateLanguageList();
            languageModal.classList.add('show');
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(true);
            }}
        }});
    }}

    if (closeLanguageModal) {{
        closeLanguageModal.addEventListener('click', function() {{
            languageModal.classList.remove('show');
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }});
    }}

    // Close language modal when clicking outside
    languageModal.addEventListener('click', function(e) {{
        if (e.target === languageModal) {{
            languageModal.classList.remove('show');
            if (typeof AndroidModalState !== 'undefined') {{
                AndroidModalState.setModalOpen(false);
            }}
        }}
    }});

    // Source tarball functionality
    const sourceToggle = document.getElementById('sourceToggle');
    const sourceContent = document.getElementById('sourceContent');
    const sourceTextarea = document.getElementById('sourceTextarea');
    const sourceDownload = document.getElementById('sourceDownload');

    if (sourceToggle) {{
        sourceToggle.addEventListener('click', function(e) {{
            e.preventDefault();
            const isShown = sourceContent.classList.contains('show');

            if (!isShown) {{
                // Populate textarea with source tarball
                sourceTextarea.value = SOURCE_TARBALL_BASE64;

                // Set up download
                if (typeof AndroidFileHandler !== 'undefined') {{
                    // Android API expects base64-encoded data and will decode before writing
                    // We have text bytes that need to be written as-is
                    // So: encode our bytes → API decodes → original bytes written to file
                    sourceDownload.removeAttribute('href');
                    sourceDownload.onclick = function(e) {{
                        e.preventDefault();
                        const encodedData = btoa(SOURCE_TARBALL_BASE64);
                        AndroidFileHandler.saveFile('pdf-g4-compressor-source-base64.txt', encodedData, 'text/plain');
                        return false;
                    }};
                }} else {{
                    // Standard browser download
                    const blob = new Blob([SOURCE_TARBALL_BASE64], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    sourceDownload.href = url;
                }}

                // Show content
                sourceContent.classList.add('show');
                sourceToggle.textContent = '▼ Get the source tarball in base64';
            }} else {{
                // Hide content
                sourceContent.classList.remove('show');
                sourceToggle.textContent = '▶ Get the source tarball in base64';
            }}
        }});
    }}

    // App self-download functionality
    const appDownloadToggle = document.getElementById('appDownloadToggle');
    const appDownloadContent = document.getElementById('appDownloadContent');
    const appDownloadBtn = document.getElementById('appDownloadBtn');

    if (appDownloadToggle) {{
        appDownloadToggle.addEventListener('click', function(e) {{
            e.preventDefault();
            const isShown = appDownloadContent.classList.contains('show');

            if (!isShown) {{
                appDownloadContent.classList.add('show');
                appDownloadToggle.textContent = '▼ The ultimate inception: download this app itself';
            }} else {{
                appDownloadContent.classList.remove('show');
                appDownloadToggle.textContent = '▶ The ultimate inception: download this app itself';
            }}
        }});
    }}

    if (appDownloadBtn) {{
        appDownloadBtn.addEventListener('click', function(e) {{
            e.preventDefault();

            // Use the pristine HTML saved by the loader (not the live DOM state)
            // This ensures the downloaded file is fresh, without form values or modal state
            const html = window.PRISTINE_HTML;

            // Check if running in Android WebView with file handler
            if (typeof AndroidFileHandler !== 'undefined') {{
                // Convert to base64 for Android
                const base64Html = btoa(unescape(encodeURIComponent(html)));
                AndroidFileHandler.saveFile('pdf-to-g4-compressor.html', base64Html, 'text/html');
            }} else {{
                // Standard browser download
                const blob = new Blob([html], {{ type: 'text/html' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'pdf-to-g4-compressor.html';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        }});
    }}

    // GitHub corner visibility handling for Android app
    const githubCorner = document.querySelector('.github-corner');
    if (githubCorner && typeof AndroidFileHandler !== 'undefined') {{
        // Hide GitHub corner initially when running in Android app
        githubCorner.style.display = 'none';

        // Show GitHub corner when About modal is opened
        if (showAboutBtn) {{
            const originalAboutClick = showAboutBtn.onclick;
            showAboutBtn.addEventListener('click', function(e) {{
                githubCorner.style.display = '';
            }});
        }}

        // Show GitHub corner when License modal is opened
        if (showLicenseBtn) {{
            const originalLicenseClick = showLicenseBtn.onclick;
            showLicenseBtn.addEventListener('click', function(e) {{
                githubCorner.style.display = '';
            }});
        }}

        // Show GitHub corner when Privacy modal is opened
        if (showPrivacyBtn) {{
            showPrivacyBtn.addEventListener('click', function(e) {{
                githubCorner.style.display = '';
            }});
        }}
    }}

    console.log('PDF Monochrome CCITT G4 Compressor - Ready!');

    // Start intro animation immediately
    if (typeof IntroAnimation !== 'undefined') {{
        IntroAnimation.start();
    }}

    // Help/Demo replay button
    const helpBtn = document.getElementById('helpBtn');
    if (helpBtn) {{
        helpBtn.addEventListener('click', function() {{
            // Replay demo with slower speeds:
            // - Offline prelude 10x slower (0.1 speed multiplier)
            // - PDF demo 6.25x slower (0.16 speed multiplier)
            if (typeof IntroAnimation !== 'undefined') {{
                IntroAnimation.start(0.1, 0.16);
            }}
        }});
    }}

    // Traditional Mongolian: convert mouse wheel to horizontal scroll on container
    (function() {{
        var container = document.querySelector('.container');
        if (container) {{
            container.addEventListener('wheel', function(e) {{
                if (document.body.classList.contains('mongolian-script')) {{
                    e.preventDefault();
                    container.scrollLeft += e.deltaY;
                }}
            }}, {{passive: false}});
        }}
    }})();

    // Check if browser restored form state (desktop Chrome back button)
    // This doesn't trigger bfcache event but still restores form values
    setTimeout(function() {{
        const hasRestoredState =
            (pdfFileInput && pdfFileInput.files && pdfFileInput.files.length > 0) ||
            (dpiValue && dpiValue.value !== '310') ||
            (pageRangeInput && pageRangeInput.value !== '') ||
            Array.from(document.querySelectorAll('input[name="mode"]')).some((r, i) => r.checked && i !== 0) ||
            Array.from(document.querySelectorAll('input[name="dpiMode"]')).some((r, i) => r.checked && i !== 0) ||
            Array.from(document.querySelectorAll('input[name="pageSize"]')).some((r, i) => r.checked && i !== 0);

        if (hasRestoredState) {{
            console.log('Browser restored form state - resetting to defaults');
            resetAppState();
        }}
    }}, 100);  // Small delay to let browser finish restoring
}});
</script>
"""

    # Replace placeholders
    full_html = html_template.replace('{{JAVASCRIPT}}', js_section)
    full_html = full_html.replace('{{MONGOLIAN_FONT_BASE64}}', mongolian_font_b64)
    full_html = full_html.replace('{app_version}', read_version())

    print(f"Full application HTML: {len(full_html):,} bytes")

    # Create self-extracting loader
    final_html = create_self_extracting_loader(full_html, pako)

    # Write the output file to parent directory (project directory)
    output_path = '../../pdf-to-g4-compressor.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"✓ Built {output_path}")

    # Get file size
    size_bytes = os.path.getsize(output_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"  File size: {size_mb:.2f} MB ({size_bytes:,} bytes)")

    # Calculate total reduction
    original_size_mb = len(full_html) / (1024 * 1024)
    reduction_percent = 100 * (1 - size_bytes / len(full_html))
    print(f"  Reduction: {reduction_percent:.1f}% (from {original_size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
