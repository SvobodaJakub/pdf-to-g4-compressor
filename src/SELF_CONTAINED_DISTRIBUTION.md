# Self-Contained Distribution Strategy

This document describes the self-contained distribution approach for the PDF Monochrome CCITT G4 Compressor web application.

## Goals

1. **Single-file distribution**: The entire application is a single HTML file with all dependencies inlined
2. **Source code inclusion**: The source code is embedded within the built HTML for license compliance and user freedom
3. **Optimized size**: The HTML content is compressed to minimize download size
4. **User accessibility**: Users can extract the source code from the built HTML without external tools

## Architecture

### 1. Source Code Embedding

The complete source tree (everything in `src/` except the built HTML) is:
1. Compressed using tar with xz compression at maximum level (`tar -cJf --xz -9e`)
2. Encoded to base64
3. Embedded as a JavaScript string in the built HTML

**Why tar.xz?**
- Industry standard for source distribution
- Excellent compression ratio (LZMA2 algorithm)
- Maximum compression level (-9e) prioritizes size over compression speed
- Universally supported on Linux/macOS, available on Windows via tools

**Why base64?**
- Text-safe encoding (embeds cleanly in JavaScript/HTML)
- Universally decodable (command-line `base64 -d`, or browser APIs)
- No escaping issues with quotes or special characters

### 2. HTML Content Compression

The built HTML contains significant JavaScript code from:
- PDF.js (286KB + 1MB worker, already base64'd)
- pako (47KB) - zlib compression library
- Custom modules (g4enc.js, imageprocessing.js, pdfgen.js, etc.) - ~50KB combined

**Compression Strategy:**

Instead of compressing the entire HTML (which would require decompression before execution), we use a selective approach:

1. **Already compressed**: PDF.js worker is already base64-encoded binary
2. **Newly compressed**: Source code tarball is tar.xz + base64 (smallest possible)
3. **Not compressed**: The actual JavaScript code remains uncompressed for immediate execution

**Why not compress everything?**
- Browser needs to parse and execute JavaScript immediately
- Decompressing on load would add 1-10 second delay on every page load
- Current size (1.8MB) is acceptable for modern bandwidth
- Compression would complicate debugging and development

**Alternative considered**: Compress JavaScript modules into a zip/base64, decompress on DOMContentLoaded:
- **Pros**: 30-40% size reduction (1.8MB → ~1.2MB)
- **Cons**: 1-10 second load delay, complexity, harder debugging
- **Decision**: Not worth the tradeoff for a tool used occasionally

### 3. Source Code Access UI

In the license modal, we add:

1. **Link**: "Get the source tarball in base64"
2. **On click**: Reveals a text area with the base64-encoded tar.xz
3. **Download link**: Offers to download the base64 as a .txt file
4. **No auto-copy**: User manually selects and copies (respects user workflow)

**Extraction instructions:**
```bash
# Copy base64 from text area, save to file
cat source.txt | base64 -d > source.tar.xz
tar -xJf source.tar.xz
```

## Build Process

The `build.py` script now:

1. Reads all JavaScript modules
2. Reads template.html
3. **Creates source tarball**:
   ```bash
   tar -cJf src.tar.xz --xz -9e \
       --exclude='pdf-to-g4-compressor.html' \
       -C <project-directory> src/
   ```
4. **Encodes to base64**:
   ```python
   import base64
   with open('src.tar.xz', 'rb') as f:
       src_base64 = base64.b64encode(f.read()).decode('ascii')
   ```
5. **Embeds in HTML**:
   ```javascript
   const SOURCE_TARBALL_BASE64 = "...";
   ```
6. **Injects UI code** to display source in license modal
7. **Writes final HTML** to `../pdf-to-g4-compressor.html` (parent directory)

## File Structure

```
<project-directory>/
├── pdf-to-g4-compressor.html    # Built application (output)
├── src/                            # Source code (compressed and embedded)
│   ├── webapp_build/              # Build system
│   │   ├── build.py              # Build script (updated)
│   │   ├── template.html         # HTML template
│   │   ├── g4enc.js              # CCITT G4 encoder
│   │   ├── imageprocessing.js    # Image pipeline
│   │   ├── pdfgen.js             # PDF generation
│   │   ├── pdfcompress.js        # PDF compression
│   │   └── libs/                 # External libraries
│   ├── resources/                 # Reference code
│   ├── README.md                  # Project documentation
│   ├── LICENSES.md                # License compliance
│   ├── IMPLEMENTATION_SUMMARY.md  # Technical details
│   ├── LESSONS_LEARNED.md         # Algorithm insights
│   └── ...                        # Other documentation
├── resources/                      # Not included in tarball
└── testing_pdf_from_hell/          # Not included in tarball
```

## License Compliance

This approach satisfies Apache 2.0 license requirements:

1. **Source code availability**: Embedded in the distributed HTML
2. **License texts**: Visible in license modal and included in source
3. **Attribution**: Clearly stated in UI and documentation
4. **Modifications**: Users can extract, modify, and rebuild

## Size Analysis

**Current built HTML**: 1.76 MB (1,846,800 bytes)

**Breakdown**:
- PDF.js worker (base64): ~1.42 MB (42% of total, already compressed)
- PDF.js library: ~287 KB (8.5% of total)
- pako: ~47 KB (1.4% of total)
- Custom JavaScript: ~50 KB (1.5% of total)
- HTML/CSS: ~10 KB (0.3% of total)
- Source tarball (base64): **TBD** (~50-100 KB estimated at 9e compression)

**After embedding source**: ~1.85-1.95 MB estimated

## Future Optimizations

If size becomes a concern:

1. **Minify JavaScript**: uglify/terser could reduce custom JS by 30-50%
2. **Use PDF.js minimal build**: Exclude unused features
3. **Compress on load**: Add decompression step (tradeoff: slower startup)
4. **Split mode**: Offer "full" version with source, "lite" version without

For now, simplicity and immediate execution trump aggressive optimization.

## Development Workflow

1. Edit files in `src/webapp_build/` or `src/*.md`
2. Run `cd src/webapp_build && python3 build.py`
3. Built HTML appears in `ccitt/pdf-to-g4-compressor.html`
4. Source tarball is automatically regenerated and embedded

## Testing Source Extraction

```bash
# Open built HTML in browser
# Click "Licensed under Apache 2.0 • View Licenses & Attributions"
# Scroll to bottom, click "Get the source tarball in base64"
# Copy text from text area, save to source-base64.txt

# Extract source
base64 -d source-base64.txt > source.tar.xz
tar -xJf source.tar.xz
cd src/webapp_build
python3 build.py

# Result should be identical to original built HTML
```

---

**Implementation Status**: ✅ Complete + Self-Extracting Loader
**Last Updated**: 2026-04-02

## Implementation Notes

The self-contained distribution is now fully functional **with self-extracting loader**:

1. ✅ Source tarball creation with maximum xz compression (-9e)
2. ✅ Base64 encoding and embedding in built HTML
3. ✅ UI in license modal to reveal and download source
4. ✅ Proper exclusion of built HTML from tarball
5. ✅ Output file in project directory instead of src/
6. ✅ **Self-extracting HTML loader** (compresses entire application)

**File Sizes:**
- Source tarball (tar.xz): 537 KB
- Base64-encoded: 717 KB
- Full built HTML (uncompressed): 2.57 MB
- **Final self-extracting HTML: 1.47 MB** (40% smaller!)

**Self-Extracting Approach:**
The final HTML file is a self-extracting archive:
- Tiny loader stub with pako decompression library
- Full HTML compressed with gzip and base64-encoded
- On page load: decompresses and replaces itself (1-3 seconds)
- **Result**: 40% smaller file while remaining completely self-contained

See `SELF_EXTRACTING_HTML.md` for detailed technical documentation.

**Compression Ratio:**
- Source directory → tar.xz: ~10:1 ratio (several MB → 537 KB)
- Full HTML → gzip: 56.5% compression (2.57 MB → 1.12 MB)
- Overall distribution: 40% reduction from uncompressed HTML

**Verification:**
Tested extraction and re-build cycle:
```bash
# Extract source from built HTML
# (First decompress the loader to get full HTML)
grep "SOURCE_TARBALL_BASE64 = " <full-html> | \
  sed "s/const SOURCE_TARBALL_BASE64 = '//" | \
  sed "s/';//" | \
  base64 -d > source.tar.xz

# Extract tarball
tar -xJf source.tar.xz

# Rebuild
cd src/webapp_build
python3 build.py

# Result: Identical self-extracting HTML
```
