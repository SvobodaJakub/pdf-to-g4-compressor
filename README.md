# PDF Monochrome CCITT G4 Compressor

> **An April Fools' Day 2026 Production** 🎭  
> _"We were so preoccupied with whether we could, we didn't stop to think if we should."_

A single-file web app that compresses PDFs to monochrome (1-bit black/white) with CCITT Group 4 encoding. Works completely offline in your browser. Also contains its own source code as a base64-encoded tarball inside itself, because apparently that's a thing we do now.

**Live Demo:** https://svobodajakub.github.io/  
**GitHub:** https://github.com/SvobodaJakub/pdf-to-g4-compressor

## Why

There are plenty of nice apps for scanning paper documents to PDFs, and plenty of apps for rotating PDF pages. But very few nice apps let you drastically compress scanned PDFs with the highly efficient CCITT Group 4 compression - which can shrink files by 95%+ while maintaining perfect black-and-white clarity.

Also, someone asked "can we make a single HTML file that contains its own source code as a compressed tarball?" and instead of saying "no, that's absurd," we said "hold my coffee."

## What it does

Converts any PDF to high-compression bilevel format:
- Renders pages at 310 DPI (configurable 72-1200)
- Converts to grayscale → normalizes → bilevel (1-bit)
- Compresses with CCITT Group 4 (ITU-T T.6)
- Outputs PDF/A-1B compliant files
- Typical result: 10-80 KB per text page

## Usage

**Just open the file:**
```bash
# Double-click pdf-to-g4-compressor.html, or:
xdg-open pdf-to-g4-compressor.html
```

That's it. No installation, no server, no internet needed.

**For PWA install** (optional):
```bash
python3 -m http.server 8000
# Open http://localhost:8000/pdf-to-g4-compressor.html
# Click "Install" in browser
```

## Features

- **Single HTML file** (1.9 MB) - completely self-contained
- **Zero dependencies** - works from `file://` protocol
- **Offline-first** - no external requests
- **Dithering modes** - sharp (text) or smooth (photos)
- **PDF/A-1B output** - archival quality
- **Source included** - full source code embedded in the file (because we believe in transparency, and also because we couldn't help ourselves)
- **Recursion-ready** - you could theoretically extract the source, rebuild it, extract that source, rebuild that... we don't recommend it, but we won't stop you

## How it works

Pure JavaScript implementation:
- **PDF.js** for rendering
- **Custom G4 encoder** (ported from C)
- **pako** for zlib compression
- **FlateDecode cascading** on CCITT streams (~35% extra reduction)

Pipeline: `PDF → Canvas → Grayscale → Normalize → Bilevel → G4 Encode → PDF/A-1B`

## Architecture: A Study in Questionable Decisions

The app works, but let's talk about the elephant in the HTML file: **it contains its own source code as a base64-encoded tar.xz archive**. 

Why? Because when you're compressing PDFs, why not compress your own source code too? It's compression all the way down.

The file structure is essentially:
```
┌─────────────────────────────────────┐
│ HTML file (1.47 MB)                 │
│ ┌─────────────────────────────────┐ │
│ │ Decompression loader            │ │
│ │ (shows purple spinner)          │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ gzip'd base64 application       │ │
│ │ ┌─────────────────────────────┐ │ │
│ │ │ The actual app              │ │ │
│ │ │ ┌─────────────────────────┐ │ │ │
│ │ │ │ tar.xz base64 source    │ │ │ │
│ │ │ │ (for rebuilding this)   │ │ │ │
│ │ │ └─────────────────────────┘ │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

It's like a turducken, but for web apps, and somehow smaller than the original version without the source code. Don't ask us how. We're still processing it ourselves.

## Build from source

```bash
cd src/webapp_build
python3 build.py
# Outputs: ../../pdf-to-g4-compressor.html
```

Source extraction (from distributed HTML):
1. Open `pdf-to-g4-compressor.html` in browser
2. Click "View Licenses & Attributions"
3. Click "Get the source tarball in base64"
4. Decode and extract:
   ```bash
   base64 -d source-base64.txt | tar -xJ
   ```

## License

Apache License 2.0

Third-party components:
- PDF.js (Apache 2.0) - Mozilla Foundation
- pako (MIT) - Vitaly Puzrin
- G4Enc (Apache 2.0) - BitBank Software, Inc.

See `src/LICENSES.md` for complete attribution.

---

**Generated with Claude on April 1, 2026** 🤖  
_Single-file web application • No installation required • Source code may contain nuts (and tarballs)_

**Disclaimer:** This project actually works and is production-ready. The absurdity is purely architectural. Use responsibly, or don't. We're not your supervisor.
