# PDF Monochrome CCITT G4 Compressor

A single-file web application that compresses PDFs to monochrome bilevel format with CCITT Group 4 (ITU-T T.6) compression. Works entirely offline in your browser.

**🌐 Live Demo:** https://svobodajakub.github.io/  
**📦 GitHub:** https://github.com/SvobodaJakub/pdf-to-g4-compressor

## Features

- ✅ **Single HTML file** (2.7 MB) - no installation needed
- ✅ **Completely self-contained** - includes full source code
- ✅ **Works offline** - no internet connection required
- ✅ **Configurable DPI** - 72 to 1200 DPI (310 DPI default)
- ✅ **CCITT Group 4 compression** - efficient bilevel encoding (ITU-T T.6)
- ✅ **JBIG2 compression** - optional lossy compression for maximum reduction
- ✅ **PDF/A-1B output** - archival-quality PDFs
- ✅ **FlateDecode cascading** - additional compression on CCITT streams (~35% extra reduction)
- ✅ **Dithering modes** - non-dithered (sharp) or dithered (smooth) output
- ✅ **PWA installable** - can be installed as mobile/desktop app

## Quick Start

**Open directly in browser:**
```bash
# Just double-click pdf-to-g4-compressor.html
# Or from command line:
xdg-open pdf-to-g4-compressor.html
```

**As PWA** (for offline installation):
```bash
python3 -m http.server 8000
# Then open: http://localhost:8000/pdf-to-g4-compressor.html
# Click "Install" in browser
```

## How It Works

1. **Render PDF** → Each page rendered to canvas at selected DPI
2. **Convert to grayscale** → RGB to grayscale (Rec. 601 luma)
3. **Normalize** → Histogram stretching for contrast
4. **Level adjustment** → 10% black point, 90% white point
5. **Convert to bilevel** → 1-bit black/white (threshold or Floyd-Steinberg dithering)
6. **Compress** → CCITT G4 (lossless) or JBIG2 (lossy with symbol matching)
7. **Generate PDF** → Create PDF/A-1B with compressed image streams
8. **Apply FlateDecode** → Cascade zlib compression for maximum reduction

## Usage Guide

### DPI Selection

- **310 DPI (default):** Best balance of quality and file size
- **150-200 DPI:** Smaller files for web viewing
- **600-1200 DPI:** Maximum quality for printing

All output is in one of few selectable page sizes. Higher DPI = more pixels = larger files.

### Dithering Mode

**Non-dithered (Sharp)** - Best for text, diagrams, line art
**Dithered (Smooth)** - Best for photographs, grayscale images

Both modes produce valid PDF/A-1B output with excellent compression.

### Performance

- Processing: 1-2 seconds per page @ 310 DPI
- Output: 10-80 KB per page (typical text documents)

## Source Code

The complete source code is embedded in the HTML file. To extract:

1. Open `pdf-to-g4-compressor.html` in browser
2. Click "Licensed under Apache 2.0 • View Licenses & Attributions"
3. Click "▶ Get the source tarball in base64"
4. Copy the text and save to `source-base64.txt`
5. Extract:
   ```bash
   base64 -d source-base64.txt > source.tar.xz
   tar -xJf source.tar.xz
   cd src/webapp_build
   python3 build.py
   ```

## Development

### Rebuild from Source

```bash
cd src/webapp_build
python3 build.py
# Outputs: ../../pdf-to-g4-compressor.html
```

### Architecture

- **JavaScript + WebAssembly** - Hybrid architecture for performance
- **Self-extracting** - HTML decompresses itself on load
- **PDF.js** - Mozilla PDF renderer (Apache 2.0)
- **pako** - zlib compression (MIT)
- **G4Enc** - CCITT encoder ported from C (Apache 2.0)
- **jbig2enc** - JBIG2 encoder compiled to WebAssembly via Emscripten (Apache 2.0)
- **Leptonica** - Image processing library (BSD-style, linked in jbig2enc)
- **Noto Sans Mongolian** - Traditional Mongolian script support (SIL OFL 1.1)

## License

**Apache License 2.0**

Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors

Third-party components:
- **PDF.js** (Apache 2.0) - Mozilla Foundation
- **pako** (MIT) - Vitaly Puzrin and Andrei Tuputcyn
- **G4Enc** (Apache 2.0) - BitBank Software, Inc.
- **jbig2enc** (Apache 2.0) - Adam Langley (Google Inc.)
- **Leptonica** (BSD-style) - Dan Bloomberg, Leptonica project
- **libtiff** (BSD-style) - Sam Leffler, Silicon Graphics, Inc.
- **Noto Sans Mongolian** (SIL OFL 1.1) - The Noto Project Authors

See `LICENSES.md` for complete license texts and attribution.

## Documentation

- **BUILD_SUMMARY.md** - Build process and compression details
- **LICENSES.md** - Complete license compliance
- **LESSONS_LEARNED.md** - CCITT G4 algorithm insights
- **SELF_EXTRACTING_HTML.md** - Self-extracting loader implementation

---

**PDF Monochrome CCITT G4 Compressor** • Single-file web application • Apache 2.0 License
