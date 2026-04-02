# Testing Instructions

## Quick Test

### 1. Open the Application

```bash
# Option A: Direct file access
xdg-open pdf-to-g4-compressor.html

# Option B: Local web server (better for testing)
python3 -m http.server 8000
# Then open: http://localhost:8000/pdf-to-g4-compressor.html
```

### 2. Load a PDF

1. Click "Choose PDF File" or drag & drop a PDF
2. Select conversion mode:
   - **Non-dithered (Sharp):** Best for text, documents, line art
   - **Dithered (Smooth):** Best for photographs, grayscale images
3. Click "Convert to CCITT"
4. Wait for processing (progress shown)
5. Download `yourfile_ccitt.pdf`

### 3. Verify Output

Open the downloaded PDF in any viewer. It should:
- ✅ Render correctly (bilevel black and white)
- ✅ Preserve all pages from original
- ✅ Be smaller than original (typically)
- ✅ Be PDF/A-1b compliant (if checked with veraPDF)

## Detailed Testing

### Browser Console Checks

Open Developer Tools (F12) → Console tab.

**Expected initialization messages:**
```
PDF.js worker configured from inline code
PDF Monochrome CCITT G4 Compressor - Initializing...
DOM elements loaded: {pdfFileInput: true, convertBtn: true, uploadArea: true, ...}
PDF Monochrome CCITT G4 Compressor - Ready!
```

**During conversion (example):**
```
File selected: File {name: 'test.pdf', size: 1234567, ...}
Button enabled
Loading PDF, size: 1234567 bytes
PDF loaded, pages: 5

Page 1 rendered: 2478x3504 centered on 2478x3507 canvas
Page 1 bilevel: 2478x3507, bytesPerRow: 310
G4 encoding complete at line 3507
Page 1 G4 compressed: 10234 bytes (ratio: 0.9%)
Page 1 G4 stream: 10234 bytes, first 20 bytes: 0x1f 0xff ...

[... pages 2-5 ...]

Successfully processed 5 page(s)
Compressed 5 streams, cascaded 5, skipped 8
Original: 550000 bytes, Compressed: 340000 bytes
```

### Test Suite

**Recommended test files:**

1. **Simple text document** (1-5 pages)
   - Expected: 10-15KB per page
   - Ratio: 1-2% (excellent compression)
   - Mode: Non-dithered works best

2. **Scanned document with images**
   - Expected: 50-200KB per page
   - Ratio: 5-20% (good compression)
   - Mode: Try both, compare quality

3. **Mixed orientation** (portrait + landscape)
   - All pages should render at 310 DPI
   - Landscape pages centered on A4 canvas
   - White letterboxing where needed

4. **Large PDF** (20+ pages)
   - Should process all pages
   - Memory usage reasonable
   - No crashes or hangs

**Comprehensive test:**
- Use `testing_pdf_from_hell/hell.pdf` (49 pages, edge cases)
- Expected: 100% success rate (all pages render correctly)

## What to Check

### File Size Verification

```bash
# Check output file size
ls -lh yourfile_ccitt.pdf

# Extract images for inspection
pdfimages -ccitt yourfile_ccitt.pdf extracted
ls -lh extracted-*.tif
```

### PDF/A-1b Compliance

```bash
# Using veraPDF (if installed)
verapdf --flavour 1b yourfile_ccitt.pdf
# Expected: PASS
```

### Image Properties

```bash
# Check with pdfimages
pdfimages -list yourfile_ccitt.pdf
# Expected:
# - Type: image
# - Filter: CCITTFaxDecode/FlateDecode
# - Width: 2478 (A4 @ 310 DPI)
# - Color: gray (1-bit)
```

## Common Scenarios

### Text Documents
- **Input:** Multi-page PDF with text, diagrams
- **Mode:** Non-dithered (Sharp)
- **Expected:** 10-15KB per page, crisp text
- **Typical ratio:** 1-2%

### Photographs
- **Input:** Scanned photos, grayscale images
- **Mode:** Dithered (Smooth)
- **Expected:** 50-100KB per page, smooth gradients
- **Typical ratio:** 5-10%

### Mixed Content
- **Input:** Document with text + photos
- **Mode:** Try both, choose based on preference
- **Expected:** 20-50KB per page
- **Typical ratio:** 2-5%

## Troubleshooting

### No Output PDF

**Check console for errors:**
- Red error messages indicate JavaScript problems
- Look for "Loading PDF failed" or similar

**Common fixes:**
- Try a different PDF
- Refresh browser and retry
- Clear browser cache
- Try different browser (Chrome, Firefox, Safari)

### Corrupted Output

**Symptoms:** PDF won't open or shows garbage
- Check console for encoding errors
- Verify input PDF is valid (can other tools read it?)
- Report issue with problematic PDF

**Should never happen with current code** (all known bugs fixed)

### High Compression Ratios

**If output is larger than input:**
- Check content type (noise images compress poorly)
- Try non-dithered mode
- This is expected for incompressible random patterns

**Normal ranges:**
- Text: 1-2% (excellent)
- Photos: 5-15% (good)
- Mixed: 2-10% (good)
- Noise: >100% (expected - incompressible)

### Performance Issues

**If processing is slow (>10 seconds per page):**
- Normal for large images or complex content
- Check browser memory (F12 → Memory tab)
- Close other tabs to free memory

**Typical performance:**
- Simple pages: 1-2 seconds
- Complex pages: 2-5 seconds
- Very large PDFs: May take minutes

## Rebuilding After Changes

If you modify the JavaScript modules:

```bash
cd webapp_build
# Edit g4enc.js, imageprocessing.js, pdfgen.js, or pdfcompress.js
python3 build.py
# Rebuilds ../pdf-to-g4-compressor.html (1.75 MB)
```

**What gets inlined:**
- All JavaScript modules
- pako (zlib compression)
- PDF.js and PDF.js worker (base64 encoded)
- Result: Single 1.75 MB HTML file, no external dependencies

## Success Criteria

The application is working correctly if:
- ✅ Processes PDFs without errors
- ✅ Output PDFs open and display correctly
- ✅ Compression ratios are reasonable (1-15% for most content)
- ✅ Console shows no errors
- ✅ Both dithered and non-dithered modes work
- ✅ Multi-page PDFs preserve all pages
- ✅ Output is PDF/A-1b compliant

## Advanced Testing

### Memory Usage

Monitor browser memory while processing large PDFs:
1. F12 → Memory tab
2. Take heap snapshot before processing
3. Process PDF
4. Take heap snapshot after
5. Compare (should release memory after download)

### Browser Compatibility

Test in multiple browsers:
- **Chrome/Edge (Chromium):** Reference implementation
- **Firefox:** Verify compatibility
- **Safari:** Test on macOS/iOS
- **Mobile browsers:** Test responsive design

### PWA Installation

If served over HTTPS or localhost:
1. Look for "Install" icon in address bar
2. Install as app
3. Test offline functionality
4. Verify manifest.json is loaded

## Known Limitations

- **Browser memory:** Very large PDFs (>100MB) may cause memory issues
- **File protocol:** PWA features require HTTP/HTTPS (basic functionality works with file://)
- **Noise images:** Pure random patterns will compress poorly (expected)

## Getting Help

If you encounter issues not covered here:
1. Check browser console for detailed errors
2. Review **LESSONS_LEARNED.md** for algorithm-specific guidance
3. Verify file sizes match expected values (1.75 MB HTML)
4. Try with the test suite: `testing_pdf_from_hell/hell.pdf`

---

**Current Status:** ✅ Production Ready (both modes)  
**Version:** 1.0  
**Last Updated:** 2026-04-02
