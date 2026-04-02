# VM/WebAssembly Approach Study
## Alternative Implementation Strategies for Browser-Based PDF Processing

**Purpose**: Document the technical requirements, challenges, and implementation complexity of running the existing native toolchain (GraphicsMagick, Python) in a browser environment.

**Status**: Study only - NOT the chosen implementation approach (we're using pure JavaScript instead)

---

## Approach 1: WebAssembly Compilation

### Overview
Compile the existing C/C++ toolchain (GraphicsMagick + dependencies) to WebAssembly (WASM), creating a browser-executable binary.

### Technical Architecture

#### Components to Compile
1. **GraphicsMagick** (core)
   - C/C++ codebase (~500K lines of code)
   - Image processing engine
   - Format parsers (PDF, TIFF, PNG, JPEG, etc.)

2. **GraphicsMagick Dependencies**
   - **Ghostscript** (~1M lines) - PDF rendering via PostScript interpreter
   - **libtiff** - TIFF reading/writing
   - **libpng** - PNG support
   - **libjpeg** or **libjpeg-turbo** - JPEG codec
   - **zlib** - Compression
   - **freetype** - Font rendering
   - **lcms2** or **lcms** - Color management
   - **libxml2** - XML parsing
   - **Optional**: jbig, webp, openjp2, etc.

3. **Python Interpreter** (for our scripts)
   - CPython (~400K lines)
   - OR: Compile Python scripts to C via Nuitka/Cython first

#### Build Toolchain
- **Emscripten** - LLVM-based C/C++ to WebAssembly compiler
  - Version: Latest stable (3.1.x+)
  - Toolchain size: ~1.5 GB download
  - Build time: Several hours (full rebuild)

#### Compilation Steps
1. **Setup Emscripten SDK**
   ```bash
   git clone https://github.com/emscripten-core/emsdk.git
   cd emsdk
   ./emsdk install latest
   ./emsdk activate latest
   source ./emsdk_env.sh
   ```

2. **Compile Dependencies (bottom-up)**
   ```bash
   # Each dependency must be compiled with emcc
   emcc -O3 -o zlib.wasm zlib/*.c
   emcc -O3 -o libpng.wasm libpng/*.c -I zlib/
   emcc -O3 -o libjpeg.wasm libjpeg/*.c
   emcc -O3 -o libtiff.wasm libtiff/*.c -I zlib/ -I libjpeg/
   emcc -O3 -o freetype.wasm freetype/src/**/*.c
   # ... repeat for all deps
   ```

3. **Compile Ghostscript**
   ```bash
   # Ghostscript is MASSIVE and complex
   cd ghostscript-10.x
   emconfigure ./configure \
     --disable-threading \
     --disable-cups \
     --disable-dbus \
     --disable-gtk \
     CFLAGS="-O3"
   emmake make
   # Results in ghostscript.wasm (~20-50 MB)
   ```

4. **Compile GraphicsMagick**
   ```bash
   cd graphicsmagick-1.3.x
   emconfigure ./configure \
     --enable-shared=no \
     --enable-static=yes \
     --without-perl \
     --without-x \
     --with-gslib=yes \
     --with-zlib=yes \
     --with-png=yes \
     --with-jpeg=yes \
     --with-tiff=yes \
     CFLAGS="-O3"
   emmake make
   # Link all deps together
   emcc -O3 -o gm.wasm \
     magick/.libs/*.o \
     coders/.libs/*.o \
     -L ghostscript/ -lgs \
     -L libtiff/ -ltiff \
     -L libpng/ -lpng \
     -L zlib/ -lz \
     # ... all other deps
     -s WASM=1 \
     -s ALLOW_MEMORY_GROWTH=1 \
     -s INITIAL_MEMORY=64MB \
     -s MAXIMUM_MEMORY=4GB \
     -s EXPORTED_FUNCTIONS='["_main","_MagickReadImage",...]' \
     -s EXTRA_EXPORTED_RUNTIME_METHODS='["FS","callMain"]'
   ```

5. **Compile Python Scripts** (Option A: Include Python)
   ```bash
   # Compile CPython to WASM
   cd cpython-3.11.x
   emconfigure ./configure --enable-optimizations
   emmake make
   # Results in python.wasm (~10-20 MB)

   # Bundle our scripts
   emcc -O3 \
     --embed-file tiff2pdf_img2pdf.py \
     --embed-file pdf_compress.py \
     -o python_scripts.wasm python.wasm
   ```

5. **Compile Python Scripts** (Option B: Transpile to C)
   ```bash
   # Use Nuitka to convert Python → C
   nuitka3 --module tiff2pdf_img2pdf.py
   nuitka3 --module pdf_compress.py

   # Then compile with emcc
   emcc -O3 -o pdf_pipeline.wasm \
     tiff2pdf_img2pdf.c \
     pdf_compress.c
   ```

#### JavaScript Wrapper
```javascript
// Load WASM modules
const GraphicsMagick = await loadWASM('gm.wasm');
const PythonRuntime = await loadWASM('python.wasm');

// Initialize virtual filesystem
const FS = GraphicsMagick.FS;
FS.writeFile('/input.pdf', pdfBytes);

// Execute GraphicsMagick
GraphicsMagick.callMain([
  'convert',
  '-density', '310',
  '/input.pdf',
  '-despeckle',
  '-colorspace', 'gray',
  '+dither',
  '-colors', '2',
  '-normalize',
  '-level', '10%,90%',
  '-type', 'Bilevel',
  '-compress', 'Group4',
  '/output.tif'
]);

// Read TIFF output
const tiffBytes = FS.readFile('/output.tif');

// Run Python scripts
PythonRuntime.callMain([
  'python',
  'tiff2pdf_img2pdf.py',
  '/output.tif',
  '/output_uncompressed.pdf'
]);

const uncompressedPDF = FS.readFile('/output_uncompressed.pdf');

PythonRuntime.callMain([
  'python',
  'pdf_compress.py',
  '/output_uncompressed.pdf',
  '/final.pdf'
]);

const finalPDF = FS.readFile('/final.pdf');
```

### File Size Estimates
| Component | Compiled Size |
|-----------|--------------|
| Ghostscript.wasm | 20-50 MB |
| GraphicsMagick.wasm | 10-20 MB |
| libtiff.wasm | 500 KB |
| libpng.wasm | 200 KB |
| libjpeg.wasm | 300 KB |
| zlib.wasm | 100 KB |
| freetype.wasm | 1-2 MB |
| Python.wasm (if included) | 10-20 MB |
| **Total** | **50-100 MB** |

With gzip compression (HTTP): ~15-30 MB

### Challenges & Issues

#### 1. Build Complexity ⚠️⚠️⚠️
- **Extreme difficulty**: Each dependency has unique build quirks
- **Configure scripts**: Many use autoconf which may not work with emconfigure
- **Patches needed**: Most libraries need Emscripten-specific patches
- **Debugging**: Compiler errors are cryptic, hard to debug
- **Time investment**: Weeks to months to get working
- **Fragility**: Breaks with Emscripten updates

#### 2. Ghostscript Specifics ⚠️
- **Massive codebase**: 1M+ lines, extremely complex
- **Platform assumptions**: Expects POSIX, file I/O, etc.
- **Threading**: May use threads (not fully supported in WASM)
- **Security**: Ghostscript has had many vulnerabilities
- **Build time**: 30+ minutes just for Ghostscript

#### 3. Memory Management
- **Linear memory**: WebAssembly uses single flat memory space
- **Growth overhead**: Growing memory is expensive
- **No shared memory** (without threading): Each module needs own memory
- **Peak usage**: Processing large PDFs could hit 1-2 GB
- **Mobile limits**: iOS Safari caps WASM memory at ~1 GB

#### 4. Performance Issues
- **Initialization**: Loading 50-100 MB takes 5-15 seconds
- **JIT warmup**: First run is slow, subsequent runs faster
- **Memory copies**: JS ↔ WASM boundary copies data (slow)
- **No SIMD** (without explicit support): Slower than native
- **Typical performance**: 30-50% of native speed

#### 5. Filesystem Emulation
- **MEMFS**: In-memory filesystem (doubles memory usage)
- **Async I/O**: Can't use in synchronous WASM calls
- **Path issues**: Windows vs Unix paths in virtual FS
- **Cleanup**: Must manually delete files to free memory

#### 6. Maintenance Nightmare
- **Emscripten updates**: Break compatibility regularly
- **Upstream changes**: GM/Ghostscript updates require recompile
- **Debug difficulty**: No debugger support in many browsers
- **Error messages**: Lost in translation from C → WASM → JS

#### 7. Browser Compatibility
- **Safari issues**: Slower WASM, stricter memory limits
- **Firefox**: Better WASM support, but still limitations
- **Mobile browsers**: Limited memory, may crash
- **file:// protocol**: WASM may not load from file://

### Advantages (Why someone might choose this)
1. ✅ **Zero porting effort** - Use existing binaries as-is
2. ✅ **Feature completeness** - All GM features available
3. ✅ **Proven quality** - Battle-tested code
4. ✅ **Complex PDF support** - Ghostscript handles everything

### Disadvantages (Why we're NOT doing this)
1. ❌ **Massive file size** (50-100 MB vs 3-5 MB for pure JS)
2. ❌ **Extreme build complexity** (weeks of work)
3. ❌ **Fragile build process** (breaks easily)
4. ❌ **Poor mobile support** (memory limits, slow)
5. ❌ **Maintenance burden** (constant rebuilds)
6. ❌ **Debugging nightmare** (no good tools)
7. ❌ **Security concerns** (Ghostscript vulnerabilities)
8. ❌ **Slow initialization** (5-15 seconds)

---

## Approach 2: Browser-Based Linux VM (v86)

### Overview
Run an entire Linux kernel + userspace in the browser using the v86 x86 emulator, then execute the native tools inside the VM.

### Technical Architecture

#### Core Components
1. **v86 Emulator**
   - JavaScript x86 emulator
   - Runs in browser
   - ~500 KB minified
   - URL: https://github.com/copy/v86

2. **Linux Kernel**
   - Minimal kernel (e.g., BuildRoot or Alpine Linux)
   - Size: 5-10 MB compressed
   - x86 or x86_64 architecture

3. **Root Filesystem**
   - BusyBox or Alpine userspace
   - GraphicsMagick binary
   - Python interpreter
   - All dependencies (.so libs)
   - Size: 50-200 MB

4. **9p Filesystem** (for file sharing)
   - Protocol for JS ↔ VM file sharing
   - Slower than native filesystem

#### Build Process

##### 1. Create Minimal Linux Image
```bash
# Using BuildRoot
git clone https://github.com/buildroot/buildroot
cd buildroot
make menuconfig
# Select:
# - Target: x86_64
# - Kernel: Linux 5.15.x
# - Init: BusyBox
# - Packages: graphicsmagick, ghostscript, python3

make
# Results in:
# - bzImage (kernel, ~5 MB)
# - rootfs.ext2 (filesystem, ~100-200 MB)
```

##### 2. Optimize Image
```bash
# Strip unnecessary files
mount -o loop rootfs.ext2 /mnt
cd /mnt
rm -rf usr/share/doc usr/share/man
rm -rf usr/include  # No compilers needed
strip bin/* sbin/* usr/bin/* usr/sbin/*
# Reduce to ~50-80 MB

# Compress
cd ..
gzip -9 rootfs.ext2
# Results in rootfs.ext2.gz (~20-40 MB)
```

##### 3. Convert to Browser Format
```bash
# v86 uses its own image format
python3 tools/build_disk.py rootfs.ext2.gz rootfs.img

# Kernel also needs conversion
python3 tools/build_bzimage.py bzImage bzImage.bin
```

#### JavaScript Integration
```javascript
// Initialize v86
const emulator = new V86Starter({
  wasm_path: "v86.wasm",
  memory_size: 512 * 1024 * 1024, // 512 MB RAM
  vga_memory_size: 8 * 1024 * 1024,

  // Boot Linux
  bzimage: {
    url: "bzImage.bin",
    async: false,
  },
  filesystem: {
    baseurl: "rootfs.img",
    basefs: "rootfs.img",
  },

  autostart: true,
});

// Wait for boot (30-60 seconds!)
await new Promise(resolve => {
  emulator.add_listener("emulator-ready", resolve);
});

// Upload PDF to VM via 9p
emulator.create_file("/tmp/input.pdf", pdfBytes);

// Execute command in VM
emulator.serial0_send("gm convert -density 310 /tmp/input.pdf /tmp/output.tif\n");

// Wait for completion (no good way to detect!)
await sleep(60000); // Just wait 60 seconds...

// Run Python scripts
emulator.serial0_send("python3 /usr/local/bin/tiff2pdf_img2pdf.py /tmp/output.tif /tmp/out.pdf\n");
await sleep(30000);

emulator.serial0_send("python3 /usr/local/bin/pdf_compress.py /tmp/out.pdf /tmp/final.pdf\n");
await sleep(30000);

// Download result
const result = emulator.read_file("/tmp/final.pdf");
```

### File Size Breakdown
| Component | Size (Compressed) |
|-----------|------------------|
| v86.wasm | 500 KB |
| bzImage.bin (Linux kernel) | 5-8 MB |
| rootfs.img (filesystem) | 30-100 MB |
| Our scripts (embedded) | 50 KB |
| **Total** | **35-110 MB** |

### Challenges & Issues

#### 1. Boot Time ⚠️⚠️⚠️
- **30-60 seconds** just to boot Linux
- User must wait staring at boot messages
- No progress indication possible
- May appear "broken" to users

#### 2. Execution Speed ⚠️⚠️⚠️
- **Emulation overhead**: 50-100x slower than native
- A 5-second native operation → 4-8 minutes in VM
- **No JIT acceleration** in x86 emulator
- **No hardware acceleration** (no GPU, no SIMD)

#### 3. Communication Complexity ⚠️
- **Serial console**: Only way to interact
- **No programmatic API**: Parse text output
- **Race conditions**: Don't know when command completes
- **Error handling**: Parse stderr from console logs
- **File transfer**: Slow via 9p protocol

#### 4. Memory Usage
- **Static allocation**: Must allocate full VM RAM upfront
- **Double buffering**: Files exist in JS heap AND VM memory
- **No memory sharing**: Copies everywhere
- **Minimum 512 MB** for GM to run comfortably
- **Mobile browsers**: Will crash

#### 5. Filesystem Issues
- **9p performance**: Very slow (10-100x slower than native FS)
- **Synchronization**: Hard to know when files are written
- **Path mapping**: Complex JS ↔ VM path translation
- **Persistent storage**: None (reboot = data loss)

#### 6. Debugging
- **Black box**: Can't debug inside VM easily
- **No breakpoints**: Serial console only
- **Log hell**: Parse text output for errors
- **Crashes**: VM can crash with no useful error

#### 7. User Experience ⚠️⚠️⚠️
- **Terrible UX**: Stare at Linux boot for 1 minute
- **No progress**: Can't show real progress during GM execution
- **Appears frozen**: Long operations look like hangs
- **Browser warnings**: "Page unresponsive"
- **Mobile**: Probably won't work at all

#### 8. Build Complexity
- **Linux knowledge required**: Must build custom kernel/rootfs
- **BuildRoot learning curve**: Steep
- **Dependency hell**: Get all libraries in image
- **Testing**: Slow (must reboot VM each test)
- **Disk image tools**: Platform-specific

### Advantages (Why someone might consider this)
1. ✅ **Zero code changes** - Use native binaries exactly as-is
2. ✅ **Full Linux environment** - All tools available
3. ✅ **No porting** - Run bash scripts directly
4. ✅ **Familiar debugging** - Can use Linux tools inside VM

### Disadvantages (Why we're DEFINITELY NOT doing this)
1. ❌ **Atrocious performance** (50-100x slower than native)
2. ❌ **Massive boot time** (30-60 seconds before anything happens)
3. ❌ **Large download** (35-110 MB)
4. ❌ **Terrible UX** (users see Linux boot messages)
5. ❌ **Mobile incompatible** (crashes due to memory)
6. ❌ **No progress feedback** (black box execution)
7. ❌ **Complex communication** (serial console parsing)
8. ❌ **Fragile** (VM crashes, no error recovery)
9. ❌ **Build complexity** (custom Linux images)
10. ❌ **Maintenance nightmare** (kernel updates, security patches)

---

## Approach 3: Hybrid WebAssembly (Selective Compilation)

### Overview
Compile ONLY critical performance components to WASM, implement rest in JavaScript.

### Strategy
- **WASM**: CCITT encoder, image processing kernels
- **JavaScript**: PDF parsing, PDF generation, UI, orchestration

### Components

#### Compile to WASM
1. **G4Enc** (CCITT encoder)
   - 585 lines of C
   - Simple, no dependencies
   - ~50 KB compiled
   - Easy to compile with Emscripten

2. **Image processing kernels** (optional)
   - Threshold conversion (bilevel)
   - Floyd-Steinberg dithering
   - Normalize/level adjustment
   - Could write in C for speed
   - ~200-300 lines of C
   - ~20-30 KB compiled

#### Keep as JavaScript
- PDF.js (already JS)
- PDF parsing
- PDF generation
- Canvas manipulation
- UI logic
- pako (already JS)

### Implementation Example

#### 1. Compile G4Enc
```bash
# Compile g4enc to WASM
cd resources/G4Enc/src
emcc -O3 \
  -s WASM=1 \
  -s EXPORTED_FUNCTIONS='["_G4ENC_init","_G4ENC_addLine","_G4ENC_getOutSize"]' \
  -s EXPORTED_RUNTIME_METHODS='["ccall","cwrap"]' \
  -o g4enc.js \
  g4enc.inl

# Results in:
# - g4enc.js (glue code, ~50 KB)
# - g4enc.wasm (compiled code, ~30 KB)
```

#### 2. JavaScript Wrapper
```javascript
// Load WASM module
const G4Enc = await loadG4EncWASM();

// Wrapper functions
const g4enc_init = G4Enc.cwrap('G4ENC_init', 'number',
  ['number', 'number', 'number', 'number', 'number', 'number']);
const g4enc_addLine = G4Enc.cwrap('G4ENC_addLine', 'number',
  ['number', 'number']);
const g4enc_getOutSize = G4Enc.cwrap('G4ENC_getOutSize', 'number',
  ['number']);

// Use it
function encodeG4(bilevelImageData, width, height) {
  const imagePtr = G4Enc._malloc(width * height);
  const outputPtr = G4Enc._malloc(width * height * 2); // Generous

  // Copy image data
  G4Enc.HEAP8.set(bilevelImageData, imagePtr);

  // Initialize encoder
  const result = g4enc_init(width, height, 1, 0, outputPtr, width * height * 2);

  // Encode line by line
  for (let y = 0; y < height; y++) {
    const linePtr = imagePtr + (y * width);
    g4enc_addLine(result, linePtr);
  }

  // Get compressed data
  const outSize = g4enc_getOutSize(result);
  const compressed = new Uint8Array(G4Enc.HEAP8.buffer, outputPtr, outSize);

  // Copy and cleanup
  const output = new Uint8Array(compressed);
  G4Enc._free(imagePtr);
  G4Enc._free(outputPtr);

  return output;
}
```

### File Size Estimate
| Component | Size |
|-----------|------|
| PDF.js | 2.5 MB |
| pako | 45 KB |
| g4enc.wasm | 30 KB |
| g4enc.js (glue) | 50 KB |
| Our JS code | 100 KB |
| **Total** | **2.7 MB** |

### Advantages ✅
1. ✅ **Small size** (~3 MB vs 50-100 MB)
2. ✅ **Fast initialization** (<1 second)
3. ✅ **Easy build** (just G4Enc, not entire stack)
4. ✅ **Performance critical** (WASM for CCITT encoding)
5. ✅ **Maintainable** (mostly JavaScript)
6. ✅ **Debuggable** (JavaScript debugger works)
7. ✅ **Mobile friendly** (low memory usage)

### Disadvantages ⚠️
1. ⚠️ **Still requires Emscripten** (build toolchain)
2. ⚠️ **WASM/JS boundary** (data copying overhead)
3. ⚠️ **Two languages** (C and JavaScript)
4. ⚠️ **Memory management** (malloc/free in wrapper)

### Comparison to Pure JavaScript
- **Speed**: WASM ~2-5x faster for CCITT encoding
- **Size**: +80 KB vs pure JS implementation
- **Complexity**: Moderate (build process, memory management)
- **Decision**: Only worth it if CCITT encoding is a bottleneck

---

## Approach 4: Pure JavaScript (CHOSEN APPROACH) ⭐

See `WEB_APP_IMPLEMENTATION_PLAN.md` for full details.

### Why This Wins
1. ✅ **Smallest size**: ~3-5 MB total
2. ✅ **No build complexity**: No compilers, just write code
3. ✅ **Fast initialization**: Instant, no WASM loading
4. ✅ **Fully debuggable**: Browser DevTools work perfectly
5. ✅ **Easy maintenance**: Pure JavaScript, standard tools
6. ✅ **Single file**: Everything inline in HTML
7. ✅ **Mobile friendly**: Low memory, works everywhere
8. ✅ **Works from file://**: No issues

### Only Disadvantage
- ❌ **Must implement CCITT encoder**: ~500-1000 lines of JS
- **Mitigation**: Port G4Enc from C to JS (straightforward)

---

## Decision Matrix

| Criterion | Pure JS | Hybrid WASM | Full WASM | Linux VM |
|-----------|---------|-------------|-----------|----------|
| **File Size** | 3-5 MB ⭐ | 3 MB ⭐ | 50-100 MB ❌ | 35-110 MB ❌ |
| **Build Complexity** | None ⭐ | Low ✅ | Extreme ❌ | High ❌ |
| **Init Time** | Instant ⭐ | <1s ⭐ | 5-15s ⚠️ | 30-60s ❌ |
| **Performance** | Good ⭐ | Great ⭐ | Good ✅ | Terrible ❌ |
| **Mobile Support** | Excellent ⭐ | Excellent ⭐ | Poor ⚠️ | None ❌ |
| **Maintainability** | Easy ⭐ | Moderate ✅ | Hard ❌ | Very Hard ❌ |
| **Debuggability** | Excellent ⭐ | Good ✅ | Poor ❌ | Terrible ❌ |
| **Single File** | Yes ⭐ | Yes ⭐ | Yes ✅ | Yes ✅ |
| **Works Offline** | Yes ⭐ | Yes ⭐ | Yes ✅ | Yes ✅ |
| **User Experience** | Excellent ⭐ | Excellent ⭐ | OK ✅ | Terrible ❌ |

**Legend**: ⭐ Best | ✅ Good | ⚠️ Acceptable | ❌ Poor

---

## Conclusion

### For Study Purposes
This document demonstrates that while it IS technically possible to run native binaries in the browser via WebAssembly or VM emulation, the practical costs are enormous:

1. **WebAssembly (Full)**: Months of build system work, 50-100 MB files, ongoing maintenance nightmare
2. **Linux VM**: Cool proof-of-concept, but 50-100x slower, terrible UX, unusable in practice
3. **Hybrid WASM**: Reasonable for specific hot paths, but adds complexity for marginal gains

### For Production
The **Pure JavaScript** approach is the clear winner because:
- Simplest to implement and maintain
- Smallest file size
- Best user experience
- Works everywhere (desktop, mobile, file://)
- Fully debuggable
- No build toolchain needed

The only "cost" is implementing the CCITT encoder in JavaScript, but this is straightforward given the G4Enc reference implementation (585 lines of well-commented C code).

### Learning Value
This study is valuable for understanding:
- The capabilities and limitations of WebAssembly
- The hidden complexity of "just compile it to WASM"
- Why emulation (Linux VM) rarely makes sense for production
- The importance of choosing the right tool for the job

**Bottom line**: For a single-file web app with no server, pure JavaScript is almost always the right choice. Only consider WASM for very specific performance-critical hot paths, and never for the entire application stack.
