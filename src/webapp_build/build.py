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

    print(f"  pako: {len(pako):,} bytes")
    print(f"  pdf.js: {len(pdfjslib):,} bytes")
    print(f"  pdf.worker: {len(pdfjsworker):,} bytes")
    print(f"  pdf.worker (base64): {len(pdfjsworker_b64):,} bytes")

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

4. LibTIFF - TIFFBitRevTable (used in Python source)
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
// Main Application Logic
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {{
    'use strict';

    console.log('PDF Monochrome CCITT G4 Compressor - Initializing...');

    // Initialize internationalization
    const detectedLang = detectLanguage(); // User's preferred language
    let currentLang = detectedLang;
    console.log('Detected language:', currentLang);
    applyTranslations(currentLang);

    // Get current translations for dynamic content
    let t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

    // Show "Use English" checkbox if user's preferred language is not English
    const languageSwitch = document.getElementById('languageSwitch');
    const useEnglishCheckbox = document.getElementById('useEnglishCheckbox');

    // Always show the checkbox if detected language is not English
    if (detectedLang !== 'en') {{
        languageSwitch.classList.add('show');
    }}

    // Handle language switch
    useEnglishCheckbox.addEventListener('change', function() {{
        if (this.checked) {{
            // Switch to English
            currentLang = 'en';
            applyTranslations('en');
            t = TRANSLATIONS.en;
            document.body.setAttribute('dir', 'ltr');
            updateDPIDisplay(); // Refresh DPI display with new language
        }} else {{
            // Switch back to detected language
            currentLang = detectedLang;
            applyTranslations(detectedLang);
            t = TRANSLATIONS[detectedLang] || TRANSLATIONS.en;
            updateDPIDisplay(); // Refresh DPI display with new language
        }}
    }});

    let selectedFile = null;

    // DOM elements
    const pdfFileInput = document.getElementById('pdfFile');
    const filenameDisplay = document.getElementById('filename');
    const convertBtn = document.getElementById('convertBtn');
    const progressDiv = document.getElementById('progress');
    const progressText = document.getElementById('progressText');
    const uploadArea = document.getElementById('uploadArea');
    const pageRangeContainer = document.getElementById('pageRangeContainer');
    const pageRangeInput = document.getElementById('pageRange');
    const ditherSelectedRadio = document.getElementById('ditherSelected');
    const dpiStandardRadio = document.getElementById('dpiStandard');
    const dpiCustomRadio = document.getElementById('dpiCustom');
    const dpiSliderContainer = document.getElementById('dpiSliderContainer');
    const dpiSlider = document.getElementById('dpiSlider');
    const dpiValue = document.getElementById('dpiValue');
    const dpiDimensions = document.getElementById('dpiDimensions');
    const dpiWarning = document.getElementById('dpiWarning');

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

        // Calculate A4 dimensions at this DPI (A4 = 8.27" × 11.69")
        const widthPx = Math.round(8.27 * dpi);
        const heightPx = Math.round(11.69 * dpi);
        // Use translated template with parameters
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const template = currentT.dpiDimensions || 'A4 output: {{width}}×{{height}} pixels (portrait)';
        dpiDimensions.textContent = template.replace('{{width}}', widthPx).replace('{{height}}', heightPx);

        updateDPIWarning();
    }}

    // Check DPI and dithering mode, show appropriate warnings
    function updateDPIWarning() {{
        // Get current DPI (use 310 if standard mode is selected)
        const dpi = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value);

        // Check if dithering is enabled (mode 2 or 3)
        const ditherEnabled = document.querySelector('input[name="mode"]:checked').value !== 'nodither';

        // Clear all warning classes
        dpiWarning.classList.remove('show', 'low-quality', 'high-filesize', 'high-compute');
        dpiWarning.textContent = '';

        // Get current translations
        const currentT = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

        // Check for warnings (priority: high-compute > low-quality > high-filesize)
        if (dpi > 600) {{
            // High computational intensity warning
            dpiWarning.classList.add('show', 'high-compute');
            dpiWarning.textContent = currentT.highComputeWarning || 'Warning: Processing at DPI above 600 is computationally intensive.';
        }} else if ((!ditherEnabled && dpi < 200) || (ditherEnabled && dpi < 240)) {{
            // Low quality warning
            dpiWarning.classList.add('show', 'low-quality');
            dpiWarning.textContent = currentT.lowQualityWarning || 'Warning: Low DPI may result in poor quality output.';
        }} else if ((!ditherEnabled && dpi > 400) || (ditherEnabled && dpi > 320)) {{
            // High filesize warning
            dpiWarning.classList.add('show', 'high-filesize');
            dpiWarning.textContent = currentT.highFilesizeWarning || 'Warning: High DPI will result in larger file sizes.';
        }}
    }}

    // Sync slider when user types in DPI input
    dpiValue.addEventListener('input', function() {{
        let val = parseInt(this.value);
        // Clamp to valid range
        if (val < 72) val = 72;
        if (val > 1200) val = 1200;
        if (!isNaN(val)) {{
            dpiSlider.value = val;
            updateDPIDisplay();
        }}
    }});

    dpiSlider.addEventListener('input', updateDPIDisplay);
    updateDPIDisplay(); // Initialize display

    // Show/hide DPI slider based on radio selection
    document.querySelectorAll('input[name="dpiMode"]').forEach(radio => {{
        radio.addEventListener('change', function() {{
            if (this.value === 'custom') {{
                dpiSliderContainer.classList.add('show');
            }} else {{
                dpiSliderContainer.classList.remove('show');
            }}
            updateDPIWarning();
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
        }});
    }});

    // File upload handling
    pdfFileInput.addEventListener('change', function(e) {{
        console.log('File selected:', e.target.files[0]);
        selectedFile = e.target.files[0];
        if (selectedFile) {{
            filenameDisplay.textContent = selectedFile.name;
            convertBtn.disabled = false;
            convertBtn.textContent = 'Compress to CCITT G4';
            console.log('Button enabled');
        }}
    }});

    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {{
        e.preventDefault();
        uploadArea.classList.add('dragover');
    }});

    uploadArea.addEventListener('dragleave', function() {{
        uploadArea.classList.remove('dragover');
    }});

    uploadArea.addEventListener('drop', function(e) {{
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {{
            selectedFile = e.dataTransfer.files[0];
            if (selectedFile.type === 'application/pdf') {{
                filenameDisplay.textContent = selectedFile.name;
                convertBtn.disabled = false;
                convertBtn.textContent = 'Compress to CCITT G4';
            }} else {{
                alert('Please select a PDF file');
            }}
        }}
    }});

    // Convert button
    convertBtn.addEventListener('click', async function() {{
        if (!selectedFile) return;

        const ditherMode = document.querySelector('input[name="mode"]:checked').value;
        let ditherConfig = null;

        if (ditherMode === 'dither') {{
            ditherConfig = {{ mode: 'all' }};
        }} else if (ditherMode === 'dither-selected') {{
            const pageRangeStr = pageRangeInput.value.trim();
            if (!pageRangeStr) {{
                alert('Please enter page numbers or ranges (e.g., 1, 3-5, 8)');
                return;
            }}
            try {{
                const pages = parsePageRange(pageRangeStr);
                ditherConfig = {{ mode: 'selected', pages: pages }};
            }} catch (error) {{
                alert('Invalid page range: ' + error.message);
                return;
            }}
        }} else {{
            ditherConfig = {{ mode: 'none' }};
        }}

        try {{
            // Show progress
            progressDiv.style.display = 'block';
            progressText.textContent = 'Loading PDF...';

            // Disable all controls during conversion
            convertBtn.disabled = true;
            dpiSlider.disabled = true;
            pageRangeInput.disabled = true;
            document.querySelectorAll('input[name="mode"]').forEach(radio => {{
                radio.disabled = true;
            }});
            document.querySelectorAll('input[name="dpiMode"]').forEach(radio => {{
                radio.disabled = true;
            }});

            // Get selected DPI (use 310 if standard mode is selected)
            const targetDPI = dpiStandardRadio.checked ? 310 : parseInt(dpiSlider.value);

            // Process the PDF
            await convertPDF(selectedFile, ditherConfig, targetDPI);

        }} catch (error) {{
            console.error('Conversion error:', error);
            alert('Error during conversion: ' + error.message);
        }} finally {{
            // Re-enable all controls
            progressDiv.style.display = 'none';
            convertBtn.disabled = false;
            dpiSlider.disabled = false;
            pageRangeInput.disabled = false;
            document.querySelectorAll('input[name="mode"]').forEach(radio => {{
                radio.disabled = false;
            }});
            document.querySelectorAll('input[name="dpiMode"]').forEach(radio => {{
                radio.disabled = false;
            }});
        }}
    }});

    // Parse page range string (e.g., "1, 3-5, 8, 10-12")
    function parsePageRange(rangeStr) {{
        const pages = new Set();
        const parts = rangeStr.split(',').map(s => s.trim()).filter(s => s);

        for (const part of parts) {{
            if (part.includes('-')) {{
                // Range like "3-5"
                const [start, end] = part.split('-').map(s => parseInt(s.trim(), 10));
                if (isNaN(start) || isNaN(end) || start < 1 || end < start) {{
                    throw new Error(`Invalid range: ${{part}}`);
                }}
                for (let i = start; i <= end; i++) {{
                    pages.add(i);
                }}
            }} else {{
                // Single page like "3"
                const page = parseInt(part, 10);
                if (isNaN(page) || page < 1) {{
                    throw new Error(`Invalid page number: ${{part}}`);
                }}
                pages.add(page);
            }}
        }}

        if (pages.size === 0) {{
            throw new Error('No valid pages specified');
        }}

        return pages;
    }}

    // Main conversion function
    async function convertPDF(file, ditherConfig, targetDPI) {{
        progressText.textContent = 'Reading PDF file...';

        // Read file as ArrayBuffer
        const arrayBuffer = await file.arrayBuffer();
        const pdfData = new Uint8Array(arrayBuffer);

        progressText.textContent = 'Loading PDF with PDF.js...';
        console.log('Loading PDF, size:', pdfData.length, 'bytes');

        // Render PDF pages to images
        const pages = await renderPDFPages(pdfData, ditherConfig, targetDPI);

        if (!pages || pages.length === 0) {{
            throw new Error('No pages rendered from PDF');
        }}

        console.log(`Successfully processed ${{pages.length}} page(s)`);

        progressText.textContent = 'Generating CCITT-compressed PDF...';
        const compressedPDF = createPDF(pages);

        progressText.textContent = 'Applying FlateDecode compression...';
        const finalPDF = compressPDF(compressedPDF, pako);

        progressText.textContent = 'Downloading...';

        // Download the result
        downloadFile(finalPDF, file.name.replace('.pdf', '_ccitt.pdf'));

        progressText.textContent = 'Done!';
        setTimeout(() => {{
            progressDiv.style.display = 'none';
        }}, 2000);
    }}

    // Render PDF pages using PDF.js
    async function renderPDFPages(pdfData, ditherConfig, targetDPI) {{
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

        // Calculate A4 dimensions at target DPI (A4 = 8.27" × 11.69")
        const A4_WIDTH_PX = Math.round(8.27 * targetDPI);
        const A4_HEIGHT_PX = Math.round(11.69 * targetDPI);

        const pages = [];

        // Get canvas and context for rendering
        const previewCanvas = document.getElementById('previewCanvas');
        const previewDiv = document.getElementById('debugPreview');
        const previewInfo = document.getElementById('previewInfo');

        // Debug preview disabled - uncomment to show preview during processing
        // previewDiv.style.display = 'block';

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
            progressText.textContent = `Rendering page ${{pageNum}} of ${{pdf.numPages}} @ ${{targetDPI}} DPI...`;

            const page = await pdf.getPage(pageNum);

            // Calculate scale to fit page on A4 @ 310 DPI
            const viewport72 = page.getViewport({{ scale: 1.0 }});
            const scaleX = A4_WIDTH_PX / viewport72.width;
            const scaleY = A4_HEIGHT_PX / viewport72.height;
            const scale = Math.min(scaleX, scaleY); // Fit within A4, preserving aspect ratio

            const scaledViewport = page.getViewport({{ scale: scale }});

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

            console.log(`Page ${{pageNum}} rendered: ${{Math.floor(scaledViewport.width)}}x${{Math.floor(scaledViewport.height)}} centered on ${{A4_WIDTH_PX}}x${{A4_HEIGHT_PX}} canvas`);

            // Preview info disabled - uncomment to show preview info
            // previewInfo.textContent = `Page ${{pageNum}}/${{pdf.numPages}}: ${{previewCanvas.width}}×${{previewCanvas.height}}px @ ${{targetDPI}} DPI`;

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

            progressText.textContent = `Processing page ${{pageNum}} (${{shouldDither ? 'dithered' : 'sharp'}})...`;

            // Process through image pipeline
            const processed = processImage(imageData, {{ dither: shouldDither }});

            const bytesPerRow = Math.ceil(processed.width / 8);
            console.log(`Page ${{pageNum}} bilevel: ${{processed.width}}x${{processed.height}}, bytesPerRow: ${{bytesPerRow}}`);

            progressText.textContent = `Encoding page ${{pageNum}} with CCITT Group 4...`;

            // Encode with G4
            const encoder = new G4Encoder();
            encoder.init(processed.width, processed.height, G4ENC_MSB_FIRST);

            // CRITICAL FIX: G4 encoder expects bit=1 for WHITE, but our bilevel has bit=1 for BLACK
            // Invert all bits before encoding
            const invertedData = new Uint8Array(processed.data.length);
            for (let i = 0; i < processed.data.length; i++) {{
                invertedData[i] = ~processed.data[i] & 0xFF;
            }}

            for (let y = 0; y < processed.height; y++) {{
                const rowStart = y * bytesPerRow;
                const rowData = invertedData.slice(rowStart, rowStart + bytesPerRow);
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
                data: compressedData
            }});
        }}

        return pages;
    }}

    // Download helper
    function downloadFile(data, filename) {{
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
            AndroidFileHandler.saveFile(filename, base64Data, 'application/pdf');
        }} else {{
            // Standard browser download
            const blob = new Blob([data], {{ type: 'application/pdf' }});
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
        }});
    }}

    if (closeLicenseBtn) {{
        closeLicenseBtn.addEventListener('click', function() {{
            licenseModal.classList.remove('show');
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
        }});
    }}

    if (closeAboutBtn) {{
        closeAboutBtn.addEventListener('click', function() {{
            aboutModal.classList.remove('show');
        }});
    }}

    // Close about modal when clicking outside
    aboutModal.addEventListener('click', function(e) {{
        if (e.target === aboutModal) {{
            aboutModal.classList.remove('show');
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
                    // On Android, use click handler instead of href
                    sourceDownload.removeAttribute('href');
                    sourceDownload.onclick = function(e) {{
                        e.preventDefault();
                        AndroidFileHandler.saveFile('pdf-g4-compressor-source-base64.txt', SOURCE_TARBALL_BASE64, 'text/plain');
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
    }}

    console.log('PDF Monochrome CCITT G4 Compressor - Ready!');
}});
</script>
"""

    # Replace the JavaScript placeholder
    full_html = html_template.replace('{{JAVASCRIPT}}', js_section)

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
