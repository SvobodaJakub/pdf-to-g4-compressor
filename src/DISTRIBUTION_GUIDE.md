# Distribution Guide

This guide explains what's in the distribution and how to use it.

**🌐 Try it online:** https://svobodajakub.github.io/  
**📦 Source code:** https://github.com/SvobodaJakub/pdf-to-g4-compressor

## What You Get

**Single file**: `pdf-to-g4-compressor.html` (1.47 MB)

This HTML file is completely self-contained:
- The entire PDF compression application
- Complete source code (embedded as tar.xz + base64)
- All dependencies (PDF.js, pako, G4 encoder)
- Full documentation
- License compliance information

## How to Use

### For End Users

**Just open it:**
```bash
# Double-click the file, or:
xdg-open pdf-to-g4-compressor.html
```

The application will:
1. Show a loading screen (1-3 seconds)
2. Decompress itself
3. Display the PDF compressor interface

**Features:**
- Compress PDFs to monochrome CCITT Group 4 format
- Configurable DPI (72-1200, default 310)
- Dithering options (sharp or smooth)
- Works completely offline
- No installation required

### For Developers

**Extract the source code:**

1. Open `pdf-to-g4-compressor.html` in browser
2. Click "Licensed under Apache 2.0 • View Licenses & Attributions"
3. Click "▶ Get the source tarball in base64"
4. Copy the text and save to `source-base64.txt`
5. Extract:
   ```bash
   base64 -d source-base64.txt > source.tar.xz
   tar -xJf source.tar.xz
   ```

**Rebuild:**
```bash
cd src/webapp_build
python3 build.py
```

Output: `../../pdf-to-g4-compressor.html`

## Documentation Included

All documentation is embedded in the source tarball:

### User Documentation
- **README.md** - Quick start and usage guide
- **LICENSES.md** - Complete license information

### Developer Documentation
- **BUILD_SUMMARY.md** - Build process and compression details
- **LESSONS_LEARNED.md** - CCITT G4 algorithm insights
- **SELF_EXTRACTING_HTML.md** - Self-extracting loader technical details
- **SELF_CONTAINED_DISTRIBUTION.md** - Source embedding approach

### Reference Documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical implementation details
- **TESTING_INSTRUCTIONS.md** - Testing procedures
- **WEB_APP_IMPLEMENTATION_PLAN.md** - Original design plan
- **VM_WASM_APPROACH_STUDY.md** - Alternative approaches considered

## Technical Details

### File Structure
```
pdf-to-g4-compressor.html (1.47 MB)
├── Loader HTML (~50 KB)
│   ├── Loading screen
│   └── Pako decompression library
└── Compressed Application (1.12 MB gzipped)
    ├── Full application HTML
    ├── PDF.js renderer
    ├── CCITT G4 encoder
    └── Source tarball (537 KB tar.xz + base64)
```

### Compression Details
- Full HTML: 2.57 MB
- Compressed with gzip (level 9): 1.12 MB (56.5% reduction)
- Base64 encoded: 1.49 MB
- Final with loader: **1.47 MB** (40% smaller than uncompressed)

### Browser Compatibility
- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- All modern browsers with JavaScript enabled

## License

**Apache License 2.0**

Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors

This is free and open source software. You can:
- Use it for any purpose
- Modify it
- Distribute it
- Distribute modified versions

See embedded license information for complete terms and third-party attributions.

## Support

This is an open source project distributed as-is. For issues or contributions, refer to the source repository information in the embedded license modal.

---

**PDF Monochrome CCITT G4 Compressor** • Single-file web application • Apache 2.0 License
