/**
 * PDF Stream Compressor
 * Applies FlateDecode compression to all streams in a PDF
 * Cascades FlateDecode on top of existing filters (like CCITTFaxDecode)
 *
 * Ported from pdf_compress.py (original Python code by Claude AI)
 * Requires pako.js for zlib compression
 *
 * Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Licensed under the Apache License, Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * All code is original implementation.
 * See LICENSES.md for complete attribution.
 */

'use strict';

/**
 * Compress all streams in a PDF
 * @param {Uint8Array} pdfData - Input PDF data
 * @param {object} pako - pako library reference
 * @returns {Uint8Array} Compressed PDF data
 */
function compressPDF(pdfData, pako) {
    const decoder = new TextDecoder('latin1');
    const encoder = new TextEncoder();

    // Find PDF header
    let headerEnd = 0;
    for (let i = 0; i < Math.min(100, pdfData.length); i++) {
        if (pdfData[i] === 0x0A) { // \n
            if (i > 10) { // Past %PDF-1.x and binary marker
                headerEnd = i + 1;
                break;
            }
        }
    }

    const header = pdfData.slice(0, headerEnd);

    // Find xref position
    const xrefMatch = findPattern(pdfData, encoder.encode('xref\n'));
    if (xrefMatch === -1) {
        throw new Error('Could not find xref table');
    }

    const xrefStart = xrefMatch;

    // Parse objects
    const objects = findObjects(pdfData.slice(0, xrefStart));

    // Process each object (compress streams)
    const compressedObjects = [];
    let stats = { compressed: 0, cascaded: 0, skipped: 0 };

    for (const obj of objects) {
        const result = parseStreamObject(obj.data);

        if (!result.streamData) {
            // Not a stream object
            compressedObjects.push(obj.data);
            stats.skipped++;
            continue;
        }

        const { dictData, streamData } = result;

        // Parse dictionary
        const dictInfo = parseDict(dictData);

        // Skip compression for XMP Metadata streams (PDF/A-1b requirement)
        if (dictInfo.type === 'Metadata' || dictInfo.subtype === 'XML') {
            compressedObjects.push(obj.data);
            stats.skipped++;
            continue;
        }

        // Compress stream
        const originalSize = streamData.length;
        const compressedData = pako.deflate(streamData, { level: 9 });
        const compressedSize = compressedData.length;

        // Update dictionary
        const hasExistingFilter = dictInfo.filter !== null;
        const newDict = updateDictWithCompression(
            dictData,
            compressedSize,
            true,
            dictInfo.filter
        );

        // Rebuild object
        const newObj = concatArrays([
            newDict,
            encoder.encode('\nstream\n'),
            compressedData,
            encoder.encode('\nendstream')
        ]);

        compressedObjects.push(newObj);

        if (hasExistingFilter) {
            stats.cascaded++;
        } else {
            stats.compressed++;
        }
    }

    // Rebuild PDF
    let newPdf = header;
    const offsets = [];

    for (let i = 0; i < compressedObjects.length; i++) {
        offsets.push(newPdf.length);

        const objHeader = encoder.encode(`${i + 1} 0 obj\n`);
        const objFooter = encoder.encode('\nendobj\n');

        newPdf = concatArrays([newPdf, objHeader, compressedObjects[i], objFooter]);
    }

    // Write xref table
    const xrefOffset = newPdf.length;
    let xref = encoder.encode(`xref\n0 ${compressedObjects.length + 1}\n0000000000 65535 f \n`);

    for (const offset of offsets) {
        const offsetStr = String(offset).padStart(10, '0');
        xref = concatArrays([xref, encoder.encode(`${offsetStr} 00000 n \n`)]);
    }

    newPdf = concatArrays([newPdf, xref]);

    // Copy trailer from original PDF
    const trailerMatch = findPattern(pdfData, encoder.encode('trailer\n'));
    if (trailerMatch === -1) {
        throw new Error('Could not find trailer');
    }

    const startxrefMatch = findPattern(pdfData, encoder.encode('startxref'));
    if (startxrefMatch === -1) {
        throw new Error('Could not find startxref');
    }

    const trailerDict = pdfData.slice(trailerMatch + 8, startxrefMatch);

    newPdf = concatArrays([
        newPdf,
        encoder.encode('trailer\n'),
        trailerDict,
        encoder.encode(`startxref\n${xrefOffset}\n%%EOF\n`)
    ]);

    console.log(`Compressed ${stats.compressed} streams, cascaded ${stats.cascaded}, skipped ${stats.skipped}`);
    console.log(`Original: ${pdfData.length} bytes, Compressed: ${newPdf.length} bytes`);

    return newPdf;
}

/**
 * Find all objects in PDF
 */
function findObjects(pdfData) {
    const decoder = new TextDecoder('latin1');
    const pdfStr = decoder.decode(pdfData);
    const pattern = /(\d+) 0 obj\s*/g;
    const objects = [];

    let match;
    while ((match = pattern.exec(pdfStr)) !== null) {
        const objNum = parseInt(match[1]);
        const start = match.index + match[0].length;

        // Find endobj
        const endobjIdx = pdfStr.indexOf('endobj', start);
        if (endobjIdx === -1) continue;

        const end = endobjIdx;
        const data = pdfData.slice(start, end);

        objects.push({ num: objNum, start, end, data });
    }

    return objects;
}

/**
 * Parse a stream object
 */
function parseStreamObject(objData) {
    const decoder = new TextDecoder('latin1');
    const objStr = decoder.decode(objData);

    const streamMatch = objStr.match(/stream\s*\n/);
    if (!streamMatch) {
        return { streamData: null };
    }

    const dictEnd = streamMatch.index;
    const streamStart = streamMatch.index + streamMatch[0].length;

    const endstreamMatch = objStr.substring(streamStart).match(/\s*endstream/);
    if (!endstreamMatch) {
        return { streamData: null };
    }

    const streamEnd = streamStart + endstreamMatch.index;

    const dictData = objData.slice(0, dictEnd);
    const streamData = objData.slice(streamStart, streamEnd);

    return { dictData, streamData };
}

/**
 * Parse dictionary
 */
function parseDict(dictData) {
    const decoder = new TextDecoder('latin1');
    const dictStr = decoder.decode(dictData);

    // Extract /Length
    const lengthMatch = dictStr.match(/\/Length\s+(\d+)/);
    const length = lengthMatch ? parseInt(lengthMatch[1]) : null;

    // Extract /Filter
    const filterMatch = dictStr.match(/\/Filter\s+(\/\w+|\[[^\]]+\])/);
    const filter = filterMatch ? filterMatch[1] : null;

    // Extract /Type
    const typeMatch = dictStr.match(/\/Type\s+\/(\w+)/);
    const type = typeMatch ? typeMatch[1] : null;

    // Extract /Subtype
    const subtypeMatch = dictStr.match(/\/Subtype\s+\/(\w+)/);
    const subtype = subtypeMatch ? subtypeMatch[1] : null;

    return { length, filter, type, subtype, raw: dictData };
}

/**
 * Update dictionary with compression
 */
function updateDictWithCompression(dictData, newLength, cascadeFilter, existingFilter) {
    const decoder = new TextDecoder('latin1');
    const encoder = new TextEncoder();
    let dictStr = decoder.decode(dictData);

    // Update /Length
    dictStr = dictStr.replace(/\/Length\s+\d+/, `/Length ${newLength}`);

    // Handle /Filter
    if (cascadeFilter) {
        if (existingFilter) {
            // Already has a filter - create cascaded array
            const filterMatch = dictStr.match(/\/Filter\s+(\/\w+)/);
            if (filterMatch) {
                const existing = filterMatch[1];

                // Check for /DecodeParms
                const decodeParms = dictStr.match(/\/DecodeParms\s+(<<[^>]+>>)/);

                if (decodeParms) {
                    const existingDecodeParms = decodeParms[1];

                    dictStr = dictStr.replace(
                        /\/Filter\s+\/\w+/,
                        `/Filter [ /FlateDecode ${existing} ]`
                    );

                    dictStr = dictStr.replace(
                        /\/DecodeParms\s+<<[^>]+>>/,
                        `/DecodeParms [ null ${existingDecodeParms} ]`
                    );
                } else {
                    dictStr = dictStr.replace(
                        /\/Filter\s+\/\w+/,
                        `/Filter [ /FlateDecode ${existing} ]`
                    );
                }
            }
        } else {
            // No filter - add FlateDecode
            dictStr = dictStr.replace(
                /(\/Length)/,
                '/Filter /FlateDecode $1'
            );
        }
    }

    return encoder.encode(dictStr);
}

/**
 * Find a byte pattern in data
 */
function findPattern(data, pattern) {
    outer: for (let i = 0; i <= data.length - pattern.length; i++) {
        for (let j = 0; j < pattern.length; j++) {
            if (data[i + j] !== pattern[j]) {
                continue outer;
            }
        }
        return i;
    }
    return -1;
}

/**
 * Concatenate Uint8Arrays
 */
function concatArrays(arrays) {
    const totalLength = arrays.reduce((sum, arr) => sum + arr.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;

    for (const arr of arrays) {
        result.set(arr, offset);
        offset += arr.length;
    }

    return result;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { compressPDF };
}
