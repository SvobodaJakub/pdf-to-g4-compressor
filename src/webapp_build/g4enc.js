/**
 * G4ENCODER - CCITT Group 4 (ITU T.6) Encoder
 *
 * Ported from C to JavaScript from G4Enc by Larry Bank
 * Original: https://github.com/bitbank2/G4ENC
 * Copyright 2020-2022 BitBank Software, Inc.
 * Licensed under the Apache License, Version 2.0
 *
 * JavaScript port copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Also licensed under Apache License, Version 2.0
 */

'use strict';

// Constants
const G4ENC_MSB_FIRST = 1;
const G4ENC_LSB_FIRST = 2;
// Buffer sizing for high-DPI support (up to 1200 DPI):
// A4 @ 1200 DPI = 9924×14028 pixels
// Worst case: alternating pixels = ~4962 runs/line × 19 bits/run = ~11.8KB/line
// 128KB buffer = 10× safety margin, ensures no mid-line flush at any supported DPI
const OUTPUT_BUF_SIZE = 131072; // 128KB
const G4ENC_MAX_WIDTH = 16384;  // Support up to ~1400 DPI
const REGISTER_WIDTH = 32;

// Error codes
const G4ENC_SUCCESS = 0;
const G4ENC_NOT_INITIALIZED = 1;
const G4ENC_INVALID_PARAMETER = 2;
const G4ENC_DATA_OVERFLOW = 3;
const G4ENC_IMAGE_COMPLETE = 4;

// Number of consecutive 1 bits in a byte from MSB to LSB
const bitcount = new Uint8Array([
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 0-15
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 16-31
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 32-47
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 48-63
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 64-79
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 80-95
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 96-111
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,  // 112-127
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,  // 128-143
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,  // 144-159
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,  // 160-175
    1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,  // 176-191
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,  // 192-207
    2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,  // 208-223
    3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,  // 224-239
    4,4,4,4,4,4,4,4,5,5,5,5,6,6,7,8   // 240-255
]);

// Table of vertical codes for G4 encoding (code, length pairs)
const vtable = new Uint8Array([
    3,7,  // V(-3) = 0000011
    3,6,  // V(-2) = 000011
    3,3,  // V(-1) = 011
    1,1,  // V(0)  = 1
    2,3,  // V(1)  = 010
    2,6,  // V(2)  = 000010
    2,7   // V(3)  = 0000010
]);

// Huffman codes for white pixels (terminating codes)
const huff_white = new Uint16Array([
    0x35,8,7,6,7,4,8,4,0xb,4,
    0xc,4,0xe,4,0xf,4,0x13,5,0x14,5,7,5,8,5,
    8,6,3,6,0x34,6,0x35,6,0x2a,6,0x2b,6,0x27,7,
    0xc,7,8,7,0x17,7,3,7,4,7,0x28,7,0x2b,7,
    0x13,7,0x24,7,0x18,7,2,8,3,8,0x1a,8,0x1b,8,
    0x12,8,0x13,8,0x14,8,0x15,8,0x16,8,0x17,8,0x28,8,
    0x29,8,0x2a,8,0x2b,8,0x2c,8,0x2d,8,4,8,5,8,
    0xa,8,0xb,8,0x52,8,0x53,8,0x54,8,0x55,8,0x24,8,
    0x25,8,0x58,8,0x59,8,0x5a,8,0x5b,8,0x4a,8,0x4b,8,
    0x32,8,0x33,8,0x34,8
]);

// White make-up codes
const huff_wmuc = new Uint16Array([
    0,0,0x1b,5,0x12,5,0x17,6,0x37,7,0x36,8,
    0x37,8,0x64,8,0x65,8,0x68,8,0x67,8,0xcc,9,
    0xcd,9,0xd2,9,0xd3,9,0xd4,9,0xd5,9,
    0xd6,9,0xd7,9,0xd8,9,0xd9,9,0xda,9,
    0xdb,9,0x98,9,0x99,9,0x9a,9,0x18,6,
    0x9b,9,8,11,0xc,11,0xd,11,0x12,12,
    0x13,12,0x14,12,0x15,12,0x16,12,0x17,12,
    0x1c,12,0x1d,12,0x1e,12,0x1f,12
]);

// Black terminating codes
const huff_black = new Uint16Array([
    0x37,10,2,3,3,2,2,2,3,3,
    3,4,2,4,3,5,5,6,4,6,4,7,5,7,
    7,7,4,8,7,8,0x18,9,0x17,10,0x18,10,8,10,
    0x67,11,0x68,11,0x6c,11,0x37,11,0x28,11,0x17,11,
    0x18,11,0xca,12,0xcb,12,0xcc,12,0xcd,12,0x68,12,
    0x69,12,0x6a,12,0x6b,12,0xd2,12,0xd3,12,0xd4,12,
    0xd5,12,0xd6,12,0xd7,12,0x6c,12,0x6d,12,0xda,12,
    0xdb,12,0x54,12,0x55,12,0x56,12,0x57,12,0x64,12,
    0x65,12,0x52,12,0x53,12,0x24,12,0x37,12,0x38,12,
    0x27,12,0x28,12,0x58,12,0x59,12,0x2b,12,0x2c,12,
    0x5a,12,0x66,12,0x67,12
]);

// Black make-up codes
const huff_bmuc = new Uint16Array([
    0,0,0xf,10,0xc8,12,0xc9,12,0x5b,12,0x33,12,
    0x34,12,0x35,12,0x6c,13,0x6d,13,0x4a,13,0x4b,13,
    0x4c,13,0x4d,13,0x72,13,0x73,13,0x74,13,0x75,13,
    0x76,13,0x77,13,0x52,13,0x53,13,0x54,13,0x55,13,
    0x5a,13,0x5b,13,0x64,13,0x65,13,8,11,0xc,11,
    0xd,11,0x12,12,0x13,12,0x14,12,0x15,12,0x16,12,
    0x17,12,0x1c,12,0x1d,12,0x1e,12,0x1f,12
]);

// Bit reversal table (ucMirror)
const ucMirror = new Uint8Array([
    0, 128, 64, 192, 32, 160, 96, 224, 16, 144, 80, 208, 48, 176, 112, 240,
    8, 136, 72, 200, 40, 168, 104, 232, 24, 152, 88, 216, 56, 184, 120, 248,
    4, 132, 68, 196, 36, 164, 100, 228, 20, 148, 84, 212, 52, 180, 116, 244,
    12, 140, 76, 204, 44, 172, 108, 236, 28, 156, 92, 220, 60, 188, 124, 252,
    2, 130, 66, 194, 34, 162, 98, 226, 18, 146, 82, 210, 50, 178, 114, 242,
    10, 138, 74, 202, 42, 170, 106, 234, 26, 154, 90, 218, 58, 186, 122, 250,
    6, 134, 70, 198, 38, 166, 102, 230, 22, 150, 86, 214, 54, 182, 118, 246,
    14, 142, 78, 206, 46, 174, 110, 238, 30, 158, 94, 222, 62, 190, 126, 254,
    1, 129, 65, 193, 33, 161, 97, 225, 17, 145, 81, 209, 49, 177, 113, 241,
    9, 137, 73, 201, 41, 169, 105, 233, 25, 153, 89, 217, 57, 185, 121, 249,
    5, 133, 69, 197, 37, 165, 101, 229, 21, 149, 85, 213, 53, 181, 117, 245,
    13, 141, 77, 205, 45, 173, 109, 237, 29, 157, 93, 221, 61, 189, 125, 253,
    3, 131, 67, 195, 35, 163, 99, 227, 19, 147, 83, 211, 51, 179, 115, 243,
    11, 139, 75, 203, 43, 171, 107, 235, 27, 155, 91, 219, 59, 187, 123, 251,
    7, 135, 71, 199, 39, 167, 103, 231, 23, 151, 87, 215, 55, 183, 119, 247,
    15, 143, 79, 207, 47, 175, 111, 239, 31, 159, 95, 223, 63, 191, 127, 255
]);

/**
 * G4Encoder class
 */
class G4Encoder {
    constructor() {
        this.width = 0;
        this.height = 0;
        this.y = 0;
        this.fillOrder = G4ENC_MSB_FIRST;
        this.dataSize = 0;
        this.error = G4ENC_SUCCESS;

        // Buffered bits state
        this.bb = {
            buf: new Uint8Array(OUTPUT_BUF_SIZE),
            bufPos: 0,
            bits: 0,
            bitOff: 0
        };

        // Output buffer
        this.output = [];

        // Reference and current line flips
        this.curFlips = new Int16Array(G4ENC_MAX_WIDTH);
        this.refFlips = new Int16Array(G4ENC_MAX_WIDTH);
    }

    /**
     * Initialize the encoder
     */
    init(width, height, bitDirection = G4ENC_MSB_FIRST) {
        if (width <= 0 || height <= 0 || width > G4ENC_MAX_WIDTH) {
            return G4ENC_INVALID_PARAMETER;
        }
        if (bitDirection !== G4ENC_MSB_FIRST && bitDirection !== G4ENC_LSB_FIRST) {
            return G4ENC_INVALID_PARAMETER;
        }

        this.width = width;
        this.height = height;
        this.fillOrder = bitDirection;
        this.y = 0;
        this.dataSize = 0;
        this.output = [];

        // Initialize flip arrays
        for (let i = 0; i < G4ENC_MAX_WIDTH; i++) {
            this.refFlips[i] = width;
            this.curFlips[i] = width;
        }

        // Reset buffered bits
        this.bb.bufPos = 0;
        this.bb.bits = 0;
        this.bb.bitOff = 0;

        this.error = G4ENC_SUCCESS;
        return G4ENC_SUCCESS;
    }

    /**
     * Flush current buffer to output and create new buffer
     * Can be called mid-encoding when buffer is full
     */
    flushBuffer() {
        // First, flush any complete bytes from the bit register to the buffer
        this.flushCompleteBytes();

        const len = this.bb.bufPos;
        if (len === 0) return; // Nothing to flush

        if (this.fillOrder === G4ENC_LSB_FIRST) {
            this.reverseBits(this.bb.buf, len);
        }
        this.output.push(this.bb.buf.slice(0, len));
        this.dataSize += len;

        // Create fresh buffer to avoid stale data contamination
        this.bb.buf = new Uint8Array(OUTPUT_BUF_SIZE);
        this.bb.bufPos = 0;
        // bb.bits and bb.bitOff preserved for continuity (partial bits still pending)
    }

    /**
     * Insert a code into the bit buffer
     */
    insertCode(code, len) {
        const bb = this.bb;

        if ((bb.bitOff + len) > REGISTER_WIDTH) {
            // Safety check: Ensure room for 4 bytes
            // With 32KB buffer, this should never trigger mid-line (matches C code behavior)
            // But kept as failsafe for pathological cases
            if (bb.bufPos + 4 > OUTPUT_BUF_SIZE) {
                this.flushBuffer();
            }

            // Need to write data
            bb.bits |= (code >>> (bb.bitOff + len - REGISTER_WIDTH));

            // Write 4 bytes (big-endian)
            bb.buf[bb.bufPos++] = (bb.bits >>> 24) & 0xFF;
            bb.buf[bb.bufPos++] = (bb.bits >>> 16) & 0xFF;
            bb.buf[bb.bufPos++] = (bb.bits >>> 8) & 0xFF;
            bb.buf[bb.bufPos++] = bb.bits & 0xFF;

            bb.bits = code << ((REGISTER_WIDTH * 2) - (bb.bitOff + len));
            bb.bitOff += len - REGISTER_WIDTH;
        } else {
            bb.bits |= (code << (REGISTER_WIDTH - bb.bitOff - len));
            bb.bitOff += len;
        }
    }

    /**
     * Flush buffered bits to output
     */
    flushBits() {
        const bb = this.bb;

        while (bb.bitOff >= 8) {
            bb.buf[bb.bufPos++] = (bb.bits >>> (REGISTER_WIDTH - 8)) & 0xFF;
            bb.bits <<= 8;
            bb.bitOff -= 8;
        }

        bb.buf[bb.bufPos++] = (bb.bits >>> (REGISTER_WIDTH - 8)) & 0xFF;
        bb.bitOff = 0;
        bb.bits = 0;
    }

    /**
     * Flush complete bytes from bit buffer (without padding)
     * Used when buffer is full mid-encoding
     */
    flushCompleteBytes() {
        const bb = this.bb;

        while (bb.bitOff >= 8) {
            bb.buf[bb.bufPos++] = (bb.bits >>> (REGISTER_WIDTH - 8)) & 0xFF;
            bb.bits <<= 8;
            bb.bitOff -= 8;
        }
        // Note: We do NOT flush the final partial byte or reset bits
        // Partial bits stay in the register for the next buffer
    }

    /**
     * Add white pixels run
     */
    addWhite(len) {
        while (len >= 64) {
            if (len >= 2560) {
                this.insertCode(0x1f, 12);
                len -= 2560;
            } else {
                const code = len >>> 6;
                this.insertCode(huff_wmuc[code * 2], huff_wmuc[code * 2 + 1]);
                len &= 63;
            }
        }
        this.insertCode(huff_white[len * 2], huff_white[len * 2 + 1]);
    }

    /**
     * Add black pixels run
     */
    addBlack(len) {
        while (len >= 64) {
            if (len >= 2560) {
                this.insertCode(0x1f, 12);
                len -= 2560;
            } else {
                const code = len >>> 6;
                this.insertCode(huff_bmuc[code * 2], huff_bmuc[code * 2 + 1]);
                len &= 63;
            }
        }
        this.insertCode(huff_black[len * 2], huff_black[len * 2 + 1]);
    }

    /**
     * Encode a line of pixels to run-end format
     */
    encodeLine(pixels) {
        const xsize = this.width;
        const curFlips = this.curFlips;
        let iCount = (xsize + 7) >>> 3;
        let cBits = 8;
        let iLen = 0;
        let x = 0;
        let xborder = xsize;  // Track remaining pixels for boundary checking
        let destPos = 0;
        let pixelPos = 0;

        let c = pixels[pixelPos++];
        iCount--;

        outerLoop: while (iCount >= 0) {
            let i = bitcount[c];
            iLen += i;
            c <<= i;
            c &= 0xFF;
            cBits -= i;

            if (cBits <= 0) {
                iLen += cBits;
                cBits = 8;
                c = pixels[pixelPos++];
                iCount--;
                continue;
            }

            c = (~c) & 0xFF;

            // Store white run
            xborder -= iLen;
            if (xborder < 0) {
                iLen += xborder;  // Adjust run length to not go past end
                break;
            }
            x += iLen;
            curFlips[destPos++] = x;
            iLen = 0;

            // Black pixels (doblack section)
            while (true) {
                i = bitcount[c];
                iLen += i;
                c <<= i;
                c &= 0xFF;
                cBits -= i;

                if (cBits <= 0) {
                    iLen += cBits;
                    cBits = 8;
                    c = pixels[pixelPos++];
                    c = (~c) & 0xFF;
                    iCount--;
                    if (iCount < 0) break outerLoop;  // Break from OUTER loop, skip storing black run
                    // Continue in black pixel loop (equivalent to goto doblack)
                } else {
                    break;  // Color change, exit black loop
                }
            }

            // Store black run
            c = (~c) & 0xFF;
            xborder -= iLen;
            if (xborder < 0) {
                iLen += xborder;  // Adjust run length to not go past end
                break;
            }
            x += iLen;
            curFlips[destPos++] = x;
            iLen = 0;
        }

        // Clamp to line width to prevent counting padding bits in last byte
        // For non-byte-aligned widths (e.g., 2478 = 309 bytes + 6 bits), the last
        // byte has padding bits that shouldn't be counted as valid pixels.
        x += iLen;
        if (x > xsize) x = xsize;
        curFlips[destPos++] = x;
        curFlips[destPos++] = x;
        curFlips[destPos++] = x;
        curFlips[destPos++] = x;
    }

    /**
     * Reverse bits if needed
     */
    reverseBits(data, len) {
        for (let i = 0; i < len; i++) {
            data[i] = ucMirror[data[i]];
        }
    }

    /**
     * Add a line of pixels
     */
    addLine(pixels) {
        if (!pixels) {
            return G4ENC_INVALID_PARAMETER;
        }
        if (this.fillOrder !== G4ENC_MSB_FIRST && this.fillOrder !== G4ENC_LSB_FIRST) {
            return G4ENC_NOT_INITIALIZED;
        }

        const xsize = this.width;
        const curFlips = this.curFlips;
        const refFlips = this.refFlips;
        const iHighWater = OUTPUT_BUF_SIZE - 4096; // 28KB threshold (32KB buffer) - C code uses OUTPUT_BUF_SIZE - 8
        let len; // Declare len for use in buffer flushing

        // Check if we need to flush buffer BEFORE encoding this line
        // CRITICAL: C code only flushes BETWEEN lines, never mid-line
        // 32KB buffer ensures we never flush mid-line for any realistic image (worst case ~8KB/line)
        if (this.bb.bufPos >= iHighWater) {
            this.flushBuffer();
        }

        // Encode the line
        this.encodeLine(pixels);

        // DIAGNOSTIC: Check encoding state on first line
        if (this.y === 0) {
            // Log the actual bitmap data
            const bytesPerRow = Math.ceil(xsize / 8);
            console.log(`📊 Line 0 diagnostics:`);
            console.log(`  Width: ${xsize}, BytesPerRow: ${bytesPerRow}`);
            console.log(`  First 20 bytes of bitmap (after inversion): ${Array.from(pixels.slice(0, 20)).map(b => '0x' + b.toString(16).padStart(2, '0')).join(' ')}`);

            // Decode first few pixels for clarity
            let pixelStr = '';
            for (let i = 0; i < Math.min(64, xsize); i++) {
                const byteIdx = Math.floor(i / 8);
                const bitPos = 7 - (i % 8);
                const bit = (pixels[byteIdx] >> bitPos) & 1;
                pixelStr += bit ? 'W' : 'B';
            }
            console.log(`  First 64 pixels: ${pixelStr}`);

            let runCount = 0;
            for (let i = 0; i < curFlips.length && curFlips[i] !== xsize; i++) {
                runCount++;
            }
            console.log(`  Run count: ${runCount}`);
            console.log(`  First 10 curFlips: [${Array.from(curFlips.slice(0, 10)).join(', ')}]`);
            console.log(`  First 10 refFlips: [${Array.from(refFlips.slice(0, 10)).join(', ')}]`);
            console.log(`  Buffer state: bufPos=${this.bb.bufPos}, bits=0x${this.bb.bits.toString(16)}, bitOff=${this.bb.bitOff}`);
            if (runCount > 1000) {
                console.warn(`⚠️ Line 0: ${runCount} runs (suspiciously high)`);
            }
        }

        // G4 encode
        let a0 = 0;
        let a0_c = 0;
        let iCur = 0;
        let iRef = 0;
        let iterationCount = 0; // DIAGNOSTIC

        while (a0 < xsize) {
            const b2 = refFlips[iRef + 1];
            const a1 = curFlips[iCur];

            // DIAGNOSTIC: Log first few iterations on line 0
            if (this.y === 0 && iterationCount < 5) {
                console.log(`  Iter ${iterationCount}: a0=${a0}, a0_c=${a0_c}, a1=${a1}, b2=${b2}, iCur=${iCur}, iRef=${iRef}`);
            }
            iterationCount++;

            if (b2 < a1) {
                // Pass mode
                a0 = b2;
                iRef += 2;
                if (this.y === 0 && iterationCount <= 5) console.log(`    → Pass mode, insertCode(1, 4)`);
                this.insertCode(1, 4); // Pass code = 0001
            } else {
                // Vertical or horizontal mode
                const dx = refFlips[iRef] - a1; // b1 - a1

                if (dx > 3 || dx < -3) {
                    // Horizontal mode
                    if (this.y === 0 && iterationCount <= 5) console.log(`    → Horizontal mode (dx=${dx}), insertCode(1, 3)`);
                    this.insertCode(1, 3); // Horizontal code = 001

                    if (a0_c) {
                        // Currently black
                        const blackRun = curFlips[iCur] - a0;
                        const whiteRun = curFlips[iCur + 1] - curFlips[iCur];
                        if (this.y === 0 && iterationCount <= 5) console.log(`    → Black ${blackRun}, White ${whiteRun}`);
                        this.addBlack(blackRun);
                        this.addWhite(whiteRun);
                    } else {
                        // Currently white
                        const whiteRun = curFlips[iCur] - a0;
                        const blackRun = curFlips[iCur + 1] - curFlips[iCur];
                        if (this.y === 0 && iterationCount <= 5) console.log(`    → White ${whiteRun}, Black ${blackRun}`);
                        this.addWhite(whiteRun);
                        this.addBlack(blackRun);
                    }

                    a0 = curFlips[iCur + 1];
                    if (a0 !== xsize) {
                        iCur += 2;
                        while (refFlips[iRef] !== xsize && refFlips[iRef] <= a0) {
                            iRef += 2;
                        }
                    }
                } else {
                    // Vertical mode
                    const vIdx = (dx + 3) * 2;
                    if (this.y === 0 && iterationCount <= 5) console.log(`    → Vertical mode (dx=${dx}), insertCode(vtable[${vIdx}], vtable[${vIdx+1}]) = (${vtable[vIdx]}, ${vtable[vIdx+1]})`);
                    this.insertCode(vtable[vIdx], vtable[vIdx + 1]);
                    a0 = a1;
                    a0_c = 1 - a0_c;

                    if (a0 !== xsize) {
                        if (iRef !== 0) iRef -= 2;
                        iRef++;
                        iCur++;
                        while (refFlips[iRef] <= a0 && refFlips[iRef] !== xsize) {
                            iRef += 2;
                        }
                    }
                }
            }
        }

        // Check if last line
        if (this.y === this.height - 1) {
            // Add two EOLs
            this.insertCode(1, 12);
            this.insertCode(1, 12);
            this.flushBits();

            len = this.bb.bufPos;
            if (this.fillOrder === G4ENC_LSB_FIRST) {
                this.reverseBits(this.bb.buf, len);
            }
            this.output.push(this.bb.buf.slice(0, len));
            this.dataSize += len;

            // Swap references
            const temp = this.curFlips;
            this.curFlips = this.refFlips;
            this.refFlips = temp;
            this.y++;

            return G4ENC_IMAGE_COMPLETE;
        }

        // Swap references
        const temp = this.curFlips;
        this.curFlips = this.refFlips;
        this.refFlips = temp;
        this.y++;

        return G4ENC_SUCCESS;
    }

    /**
     * Get the compressed data
     */
    getData() {
        // Concatenate all output chunks
        const totalSize = this.dataSize;
        const result = new Uint8Array(totalSize);
        let offset = 0;

        for (const chunk of this.output) {
            result.set(chunk, offset);
            offset += chunk.length;
        }

        return result;
    }

    /**
     * Get output size
     */
    getOutSize() {
        return this.dataSize;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { G4Encoder, G4ENC_MSB_FIRST, G4ENC_LSB_FIRST };
}
