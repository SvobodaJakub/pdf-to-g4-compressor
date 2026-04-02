# Lessons Learned: CCITT G4 Encoder Implementation

This document captures the complexities, pitfalls, and footguns encountered while porting the G4Enc CCITT Group 4 encoder from C to JavaScript. The code is now production-ready, but these lessons preserve important knowledge for future maintainers.

## Algorithm Overview: CCITT Group 4 (ITU-T T.6)

### What It Does
CCITT Group 4 is a lossless compression algorithm for bilevel (1-bit black and white) images, developed for fax machines. It uses **Modified Modified READ (MMR)** encoding:
- **2D encoding**: Compares current line with previous (reference) line
- **Run-end format**: Stores positions where color changes occur
- **Three encoding modes**: Vertical, Horizontal, and Pass mode
- **Huffman codes**: Variable-length codes for run lengths

### Why It's Complex
1. **Stateful encoding**: Each line depends on the previous line
2. **Bit-level operations**: Data is packed into bits, not bytes
3. **Multiple coordinate systems**: Pixel positions, run-end positions, bit positions
4. **Boundary conditions**: Partial bytes, padding bits, line endings
5. **Buffer management**: Streaming output with mid-line state transitions

## The C Source: G4Enc by BitBank Software

### Design Constraints (Critical Understanding)
The original C code was designed for **microcontrollers** with severe memory constraints:

```c
#define OUTPUT_BUF_SIZE 1024    // 1KB buffer
#define G4ENC_MAX_WIDTH 1024    // Max 1024 pixels wide
```

**Implications:**
- Buffer is large enough for one worst-case line at 1024px width
- Never flushes mid-line (only between lines)
- Simple buffer management strategy
- **Not designed for high-DPI images** (our A4 @ 310 DPI = 2478px wide)

### C Code Quirks
1. **Uses goto**: The `doblack:` label for black pixel loops
2. **Modifies global state**: bitBuffer struct is implicit
3. **No error handling**: Assumes caller validated inputs
4. **Bit order**: Designed for MSB-first (can be configured)
5. **Padding assumption**: May assume padding bits match last pixel color

## Major Pitfalls Encountered

### 1. Buffer Size for Large Images

**The Problem:**
The C code was designed for microcontrollers with 1024px max width. Modern high-DPI PDFs are much larger.

**Buffer Sizing Calculations:**

At 310 DPI (original requirement):
- A4 = 2478px wide
- Worst case: alternating pixels = ~1239 runs
- Each run: ~19 bits (horizontal mode + terminating codes)
- Total: ~1239 × 19 = 23,541 bits ≈ 2.9KB per line

At 1200 DPI (maximum supported):
- A4 = 9924px wide
- Worst case: alternating pixels = ~4962 runs
- Each run: ~19 bits
- Total: ~4962 × 19 = 94,278 bits ≈ 11.8KB per line

**The Fix:**
```javascript
const OUTPUT_BUF_SIZE = 131072;  // 128KB - handles up to 1200 DPI with 10× safety margin
const G4ENC_MAX_WIDTH = 16384;   // Support widths up to ~1400 DPI
```

**Why 128KB:**
- Supports DPI range: 72-1200
- Worst case @ 1200 DPI: ~12KB per line
- 128KB = 10× safety margin
- Allows buffer flush only between lines (matches C design)
- Still reasonable memory footprint for browsers

**Lesson:** Always calculate worst-case buffer requirements for your actual image dimensions, not the reference implementation's limits. When adding DPI configurability, recalculate buffers for the maximum supported DPI.

### 2. Mid-Line Buffer Flush Corruption

**The Problem:**
Initial fix (8KB buffer) added mid-line flushing in `insertCode()`. This created complex state management issues:

```javascript
insertCode(code, len) {
    if (bb.bufPos + 4 > OUTPUT_BUF_SIZE) {
        this.flushBuffer();  // ← Mid-line flush
    }
    // Write 4 bytes...
}
```

**Why It Breaks:**
- Bit register (bb.bits, bb.bitOff) contains partial bits from old buffer
- Buffer position arithmetic assumes continuity
- Byte alignment issues: flush can happen mid-Huffman-code
- G4 encoding doesn't respect byte boundaries

**The Insight:**
The C code **NEVER** flushes mid-line:

```c
// C code: g4enc.inl:436-437
G4ENCEncodeLine(...);  // Encode COMPLETE line first
iLen = (int)(bb.pBuf-pImage->ucFileBuf);
if (iLen >= iHighWater)  // THEN check buffer fullness
```

**The Fix:**
Don't try to solve mid-line flushing. Make the buffer big enough to never need it.

**Lesson:** Understand the original design philosophy before "improving" it. Sometimes constraints create simplicity.

### 3. Padding Bits in Non-Byte-Aligned Widths

**The Problem:**
For 2478-pixel width:
- 2478 ÷ 8 = 309.75 bytes
- 309 complete bytes = 2472 pixels
- Last byte: 6 valid pixels + 2 padding bits

The `encodeLine()` function counted all 8 bits of the last byte:

```javascript
// Result: run-end position 2480 instead of 2478
curFlips[0] = 2480  // Wrong!
curFlips[0] = 2478  // Correct
```

**Why This Caused Massive Corruption:**

```javascript
// G4 encoding compares current line with reference line
a1 = curFlips[0] = 2480  // From current line (wrong)
b2 = refFlips[0] = 2478  // From reference line (correct)

// Check: b2 < a1 → TRUE (2478 < 2480)
// → Selects "pass mode" (code: 0001)
// Should select "vertical V(0)" mode (code: 1) - lines are identical!
```

**The Cascade Effect:**
1. Line 0: Encoded with wrong mode → corrupts output
2. Line 0 becomes reference for line 1
3. Line 1: curFlips has 2480 → encodes wrong → corrupts reference
4. Error compounds exponentially through all 3507 lines
5. Result: 163% data expansion (compression became expansion!)

**The Fix:**
```javascript
// encodeLine() at end of function:
x += iLen;
if (x > xsize) x = xsize;  // Clamp to prevent padding bits
curFlips[destPos++] = x;
```

**Why Boundary Checks Failed:**
The xborder checks only execute when storing a run (at color change):

```javascript
// These checks are inside "store run" blocks:
xborder -= iLen;
if (xborder < 0) {
    iLen += xborder;  // Only runs during color change!
    break;
}
```

For all-white or all-black lines, there's no color change → boundary checks are bypassed!

**Lesson:** Validate final state, not just intermediate states. Boundary checks that depend on conditional code paths will fail on edge cases.

### 4. C Code vs. High-DPI Reality

**C Code Assumptions:**
- Image width ≤ 1024 pixels (fits in 128 bytes)
- Buffer size 1024 bytes (8× width in bytes)
- Simple documents (text, line art)
- Byte-aligned widths (or padding bits match last pixel)

**Modern Reality:**
- A4 @ 310 DPI = 2478 pixels (needs 310 bytes)
- A4 @ 1200 DPI = 9924 pixels (needs 1241 bytes)
- High-DPI rendering creates non-byte-aligned widths
- Floyd-Steinberg dithering creates worst-case patterns
- Large images need 12-15KB per line in worst case (1200 DPI)

**Our Implementation:**
- Supports 72-1200 DPI (user-configurable)
- 128KB buffer handles any DPI in range
- All output normalized to A4 portrait (8.27" × 11.69")
- Smaller pages centered with white letterboxing

**Lesson:** Don't assume reference code handles modern use cases. The C code was perfect for its design constraints, but those constraints don't apply to web apps processing high-DPI PDFs with user-configurable resolution.

## Algorithm Complexities

### Run-End Encoding Format

Instead of storing pixel data, we store positions where color changes:

```
Pixels: WWWWBBBWWW (W=white, B=black)
Widths: 4 white, 3 black, 3 white

Run-end format: [4, 7, 10]
  4: First transition (white→black)
  7: Second transition (black→white)
  10: End of line
```

**Pitfalls:**
- Must start with white (prepend imaginary white run if needed)
- Array is terminated with width value repeated 4 times
- Off-by-one errors are catastrophic (cascade through line)

### Vertical Mode Decision Tree

The encoder must choose the best mode for each run:

```javascript
// Vertical mode: current line similar to reference line
// Check if changing elements align within ±3 pixels
dx = a1 - b1;  // Distance between transitions
if (dx >= -3 && dx <= 3) {
    // Use vertical mode V(dx)
    // Codes: V(0)=1, VR(1)=011, VL(1)=010, VR(2)=000011, etc.
}

// Pass mode: reference line "passes" current position
else if (b2 < a1) {
    // Use pass mode (code: 0001)
    // Then update a0 to b2 and continue
}

// Horizontal mode: encode absolute run lengths
else {
    // Use horizontal mode (code: 001)
    // Then encode run lengths with Huffman codes
}
```

**Pitfalls:**
- a0, a1, b1, b2 are indices into different arrays (curFlips vs refFlips)
- Sign matters: VR(+) vs VL(-)
- Mode selection affects compression ratio dramatically
- Wrong mode doesn't cause errors, just poor compression (except when it cascades!)

### Bit Buffer Management

Data is written bit-by-bit into a 32-bit register, then flushed to byte buffer:

```javascript
bb.bits = 0x00000000;     // 32-bit accumulator
bb.bitOff = 0;            // Number of bits pending (0-31)
bb.buf = new Uint8Array(OUTPUT_BUF_SIZE);  // Output buffer
bb.bufPos = 0;            // Current position in buffer

// Insert code (e.g., 3-bit horizontal mode code: 001)
insertCode(0b001, 3) {
    bb.bits |= (code << (REGISTER_WIDTH - bb.bitOff - len));
    bb.bitOff += len;
    
    // Flush complete bytes when register fills
    if (bb.bitOff >= 16) {
        // Write 2 bytes, keep remaining bits
    }
}
```

**Pitfalls:**
- Bit order matters (MSB vs LSB first)
- Partial bytes remain in register across calls
- Buffer transitions must preserve bit state
- Always flush remaining bits at end of page

### Huffman Code Tables

White and black runs use different Huffman tables:

```javascript
// White run of 5 pixels: code 1100, length 4 bits
// Black run of 5 pixels: code 1011, length 4 bits

// Runs ≥ 64: make-up code + terminating code
// White run of 128 pixels:
//   Make-up 128: 10010, 5 bits
//   Terminating 0: 00110101, 8 bits
//   Total: 13 bits for run of 128
```

**Pitfalls:**
- Must split long runs (≥64) into make-up + terminating
- White and black have different tables
- Variable-length codes complicate bit packing
- Table lookup errors cause subtle corruption

## Production Deployment Gotchas

### Testing Requirements

**Minimum Test Suite:**
1. **All-white page** (tests padding bits, no color changes)
2. **All-black page** (tests inverted color logic)
3. **Single vertical line** (tests vertical mode selection)
4. **Alternating pixels** (tests worst-case buffer requirements)
5. **Large images** (tests buffer management at scale)
6. **Non-byte-aligned widths** (tests padding bit handling)

**Our Test:**
- 49-page "PDF from Hell" with every edge case we could create
- Mixed orientations, sizes, content types
- Dithered and non-dithered versions
- Result: 100% success rate after fixes

### Performance Considerations

**Bottlenecks:**
1. PDF.js rendering (CPU-bound, can't optimize much)
2. Floyd-Steinberg dithering (CPU-intensive, consider threshold instead)
3. G4 encoding (fast, ~1-2ms per page)
4. PDF generation (fast, ~0.5ms per page)

**Memory:**
- Canvas: ~26MB for A4 @ 310 DPI (2478×3507 × 4 bytes RGBA)
- Bilevel bitmap: ~869KB per page (2478×3507 ÷ 8)
- G4 output: ~10-15KB per page (typical)
- Buffer: 32KB (constant)

**Lesson:** Don't over-optimize the G4 encoder. The bottleneck is rendering, not compression.

### Browser Compatibility

**Works:**
- Chrome/Edge (Chromium): Perfect
- Firefox: Perfect
- Safari: Perfect (with some quirks in PWA mode)

**File API Gotchas:**
- `file://` protocol works for reading, but PWA features require HTTPS
- File size limits: tested up to 60MB PDFs without issues
- Memory: Browser may limit canvas size on mobile devices

## Code Maintenance Guidelines

### When Modifying encodeLine()

This function converts packed bitmap data to run-end format. It's the most error-prone part of the codebase.

**Critical Invariants:**
1. `curFlips` must start with position of first black pixel (or xsize if all-white)
2. `curFlips` must end with xsize repeated 4 times
3. All positions must be ≤ xsize (clamping is essential)
4. Array indices must stay in bounds (destPos validated)

**Test After Changes:**
- All-white line → curFlips = [xsize, xsize, xsize, xsize]
- All-black line → curFlips = [0, xsize, xsize, xsize]
- Single black pixel at position N → curFlips = [N, N+1, xsize, xsize]

### When Modifying Buffer Management

**Rules:**
1. Never flush mid-line (only at line boundaries)
2. Always flush remaining bits at end of page
3. Create fresh buffer after flush (prevent stale data)
4. Preserve bit register state (bb.bits, bb.bitOff) across flushes

**Validation:**
```javascript
// After flush:
assert(bb.bufPos === 0);  // Buffer reset
assert(bb.buf !== oldBuf); // Fresh buffer
// bb.bits and bb.bitOff preserved for continuity
```

### When Debugging Corruption

**Symptoms → Likely Causes:**

| Symptom | Likely Cause |
|---------|--------------|
| Data expansion (>100%) | Wrong encoding mode selection (check a1/b1/b2 logic) |
| Visual noise/artifacts | Padding bits being counted, or bit order issue |
| Corruption after N lines | Reference line contamination (check curFlips/refFlips swap) |
| Identical corruption across changes | Bug in encodeLine(), not buffer management |
| Random corruption | Buffer overflow, bit register corruption |

**Debugging Strategy:**
1. Add logging to first line (y === 0)
2. Check curFlips[0] === xsize for all-white first line
3. Verify curFlips and refFlips arrays
4. Log a0, a1, b1, b2 values and mode selection
5. Check first 20 bytes of G4 output
6. Compare with known-good encoder (libtiff, ImageMagick)

## References for Future Work

### Specifications
- **ITU-T T.6 (1988):** CCITT Group 4 fax compression standard
- **PDF Reference 1.7:** Section 3.3.5 (CCITTFaxDecode)
- **PDF/A-1b:** ISO 19005-1:2005

### Reference Implementations
- **libtiff** (`tif_fax3.c`): Production-quality, handles edge cases
- **G4Enc** (`g4enc.inl`): Simple, microcontroller-oriented
- **ImageMagick** (TIFF): Well-tested, can use for validation

### Tools for Validation
```bash
# Extract and validate CCITT stream from PDF
pdfimages -ccitt output.pdf test
tiffinfo test-000.tif

# Compare with ImageMagick
convert input.png -colorspace Gray -threshold 50% -compress Group4 reference.tif

# Validate PDF/A compliance
verapdf --flavour 1b output.pdf
```

## Summary

The CCITT G4 encoder is now production-ready after fixing:

1. ✅ **Buffer size:** 1024 → 32768 bytes (handles large images)
2. ✅ **Mid-line flush:** Eliminated by larger buffer
3. ✅ **Padding bits:** Clamp run-end to xsize
4. ✅ **Non-byte-aligned widths:** Handle 2478px (and any width)

**Key Takeaways:**
- Understand original design constraints before porting
- Calculate worst-case requirements for your use case
- Test edge cases: all-white, all-black, non-byte-aligned widths
- Validate final state, not just intermediate states
- Reference implementations are guides, not gospel

The code works perfectly for production use. This document ensures future maintainers understand **why** it works and what pitfalls to avoid.
