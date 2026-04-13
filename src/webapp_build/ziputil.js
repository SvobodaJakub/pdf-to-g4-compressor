/**
 * Minimal ZIP reader/writer using pako's deflateRaw/inflateRaw.
 * No external library beyond pako needed.
 *
 * Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Licensed under the Apache License, Version 2.0
 */

'use strict';

// CRC32 lookup table (IEEE polynomial)
var CRC32_TABLE = (function() {
    var table = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
        var c = n;
        for (var k = 0; k < 8; k++) {
            c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
        }
        table[n] = c;
    }
    return table;
})();

function crc32(data) {
    var crc = 0xFFFFFFFF;
    for (var i = 0; i < data.length; i++) {
        crc = CRC32_TABLE[(crc ^ data[i]) & 0xFF] ^ (crc >>> 8);
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
}

/**
 * Parse a ZIP file from an ArrayBuffer.
 * Returns array of {path: string, data: Uint8Array (uncompressed)}.
 */
function parseZip(arrayBuffer) {
    var bytes = new Uint8Array(arrayBuffer);
    var view = new DataView(arrayBuffer);
    var entries = [];

    // Find End of Central Directory record (search backwards)
    var eocdOffset = -1;
    for (var i = bytes.length - 22; i >= 0; i--) {
        if (view.getUint32(i, true) === 0x06054B50) {
            eocdOffset = i;
            break;
        }
    }
    if (eocdOffset === -1) throw new Error('Not a valid ZIP file');

    var cdOffset = view.getUint32(eocdOffset + 16, true);
    var cdEntries = view.getUint16(eocdOffset + 10, true);

    // Read central directory entries
    var offset = cdOffset;
    for (var e = 0; e < cdEntries; e++) {
        if (view.getUint32(offset, true) !== 0x02014B50) {
            throw new Error('Invalid central directory entry');
        }

        var method = view.getUint16(offset + 10, true);
        var compressedSize = view.getUint32(offset + 20, true);
        var uncompressedSize = view.getUint32(offset + 24, true);
        var nameLen = view.getUint16(offset + 28, true);
        var extraLen = view.getUint16(offset + 30, true);
        var commentLen = view.getUint16(offset + 32, true);
        var localHeaderOffset = view.getUint32(offset + 42, true);

        var nameBytes = bytes.subarray(offset + 46, offset + 46 + nameLen);
        var path = new TextDecoder().decode(nameBytes);

        // Skip directories
        if (!path.endsWith('/')) {
            // Read from local file header to get actual data offset
            var localNameLen = view.getUint16(localHeaderOffset + 26, true);
            var localExtraLen = view.getUint16(localHeaderOffset + 28, true);
            var dataOffset = localHeaderOffset + 30 + localNameLen + localExtraLen;

            var compressedData = bytes.subarray(dataOffset, dataOffset + compressedSize);

            var data;
            if (method === 0) {
                // Stored (no compression)
                data = compressedData;
            } else if (method === 8) {
                // Deflated
                data = pako.inflateRaw(compressedData);
            } else {
                throw new Error('Unsupported compression method ' + method + ' for ' + path);
            }

            entries.push({ path: path, data: data });
        }

        offset += 46 + nameLen + extraLen + commentLen;
    }

    return entries;
}

/**
 * Create a ZIP file from an array of entries.
 * Each entry: {path: string, data: Uint8Array}.
 * Returns Uint8Array of the ZIP file.
 */
function createZip(entries) {
    var localHeaders = [];
    var centralHeaders = [];
    var dataBlobs = [];
    var offset = 0;

    for (var i = 0; i < entries.length; i++) {
        var entry = entries[i];
        var nameBytes = new TextEncoder().encode(entry.path);
        var uncompressedData = entry.data;
        var uncompressedCrc = crc32(uncompressedData);
        var uncompressedLen = uncompressedData.length;

        // Compress with deflateRaw
        var compressedData = pako.deflateRaw(uncompressedData);
        var compressedLen = compressedData.length;

        // If compressed is larger, store uncompressed
        var method = 8; // deflate
        var storedData = compressedData;
        if (compressedLen >= uncompressedLen) {
            method = 0;
            storedData = uncompressedData;
            compressedLen = uncompressedLen;
        }

        // Local file header (30 + nameLen bytes)
        var localHeader = new Uint8Array(30 + nameBytes.length);
        var lv = new DataView(localHeader.buffer);
        lv.setUint32(0, 0x04034B50, true);  // signature
        lv.setUint16(4, 20, true);           // version needed (2.0)
        lv.setUint16(6, 0, true);            // flags
        lv.setUint16(8, method, true);       // compression method
        lv.setUint16(10, 0, true);           // mod time
        lv.setUint16(12, 0, true);           // mod date
        lv.setUint32(14, uncompressedCrc, true); // crc32
        lv.setUint32(18, compressedLen, true);   // compressed size
        lv.setUint32(22, uncompressedLen, true); // uncompressed size
        lv.setUint16(26, nameBytes.length, true); // filename length
        lv.setUint16(28, 0, true);           // extra field length
        localHeader.set(nameBytes, 30);

        // Central directory header (46 + nameLen bytes)
        var centralHeader = new Uint8Array(46 + nameBytes.length);
        var cv = new DataView(centralHeader.buffer);
        cv.setUint32(0, 0x02014B50, true);   // signature
        cv.setUint16(4, 20, true);            // version made by
        cv.setUint16(6, 20, true);            // version needed
        cv.setUint16(8, 0, true);             // flags
        cv.setUint16(10, method, true);       // compression method
        cv.setUint16(12, 0, true);            // mod time
        cv.setUint16(14, 0, true);            // mod date
        cv.setUint32(16, uncompressedCrc, true); // crc32
        cv.setUint32(20, compressedLen, true);   // compressed size
        cv.setUint32(24, uncompressedLen, true); // uncompressed size
        cv.setUint16(28, nameBytes.length, true); // filename length
        cv.setUint16(30, 0, true);            // extra field length
        cv.setUint16(32, 0, true);            // comment length
        cv.setUint16(34, 0, true);            // disk number start
        cv.setUint16(36, 0, true);            // internal attrs
        cv.setUint32(38, 0, true);            // external attrs
        cv.setUint32(42, offset, true);       // local header offset
        centralHeader.set(nameBytes, 46);

        localHeaders.push(localHeader);
        dataBlobs.push(storedData);
        centralHeaders.push(centralHeader);

        offset += localHeader.length + storedData.length;
    }

    // Calculate total size
    var cdOffset = offset;
    var cdSize = 0;
    for (var j = 0; j < centralHeaders.length; j++) {
        cdSize += centralHeaders[j].length;
    }

    // End of Central Directory (22 bytes)
    var eocd = new Uint8Array(22);
    var ev = new DataView(eocd.buffer);
    ev.setUint32(0, 0x06054B50, true);        // signature
    ev.setUint16(4, 0, true);                  // disk number
    ev.setUint16(6, 0, true);                  // disk with CD
    ev.setUint16(8, entries.length, true);      // entries on disk
    ev.setUint16(10, entries.length, true);     // total entries
    ev.setUint32(12, cdSize, true);            // CD size
    ev.setUint32(16, cdOffset, true);          // CD offset
    ev.setUint16(20, 0, true);                 // comment length

    // Assemble final ZIP
    var totalSize = cdOffset + cdSize + 22;
    var result = new Uint8Array(totalSize);
    var pos = 0;

    for (var k = 0; k < localHeaders.length; k++) {
        result.set(localHeaders[k], pos);
        pos += localHeaders[k].length;
        result.set(dataBlobs[k], pos);
        pos += dataBlobs[k].length;
    }
    for (var l = 0; l < centralHeaders.length; l++) {
        result.set(centralHeaders[l], pos);
        pos += centralHeaders[l].length;
    }
    result.set(eocd, pos);

    return result;
}
