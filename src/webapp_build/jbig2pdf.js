/**
 * JBIG2 to PDF/A-1B Converter
 * Takes jbig2enc output (global symbol dictionary + page segments) and wraps in PDF/A
 *
 * Based on jbig2topdf.py from the jbig2enc project:
 *   Copyright 2006 Google Inc. All Rights Reserved.
 *   Author: agl@imperialviolet.org (Adam Langley)
 *   Licensed under the Apache License, Version 2.0
 *   https://github.com/agl/jbig2enc
 *
 * JavaScript port and PDF/A-1B structure:
 *   Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 *   Licensed under the Apache License, Version 2.0
 */

/**
 * Parse JBIG2 file header to extract page dimensions
 * @param {Uint8Array} jbig2Data - JBIG2 file data
 * @returns {{width: number|null, height: number|null}}
 */
function readJBIG2Metadata(jbig2Data) {
    if (jbig2Data.length < 13) {
        return { width: null, height: null };
    }

    // JBIG2 file header: 0x97 0x4A 0x42 0x32 0x0D 0x0A 0x1A 0x0A
    const magic = [0x97, 0x4a, 0x42, 0x32, 0x0d, 0x0a, 0x1a, 0x0a];
    let offset = 0;

    // Check for JBIG2 file header
    let hasHeader = true;
    for (let i = 0; i < 8; i++) {
        if (jbig2Data[i] !== magic[i]) {
            hasHeader = false;
            break;
        }
    }

    if (hasHeader) {
        // Skip header (13 bytes: 8 magic + 1 flags + 4 page count)
        offset = 13;
    }

    // Read segments to find page information segment (type 48 or 49)
    let width = null;
    let height = null;

    while (offset < jbig2Data.length - 11) {
        if (offset + 5 > jbig2Data.length) break;

        // Segment header: 4 bytes segment number, 1 byte flags
        const segNum = (jbig2Data[offset] << 24) | (jbig2Data[offset + 1] << 16) |
                       (jbig2Data[offset + 2] << 8) | jbig2Data[offset + 3];
        const flags = jbig2Data[offset + 4];
        const segType = flags & 0x3f;

        offset += 5;

        // Read referenced segment count
        if (offset >= jbig2Data.length) break;
        const refSegCountByte = jbig2Data[offset];
        offset += 1;

        let refCount;
        if ((refSegCountByte >> 5) === 7) {
            // Long form
            if (offset + 4 > jbig2Data.length) break;
            refCount = ((jbig2Data[offset] << 24) | (jbig2Data[offset + 1] << 16) |
                       (jbig2Data[offset + 2] << 8) | jbig2Data[offset + 3]) & 0x1fffffff;
            offset += 4;
        } else {
            // Short form
            refCount = refSegCountByte >> 5;
        }

        // Skip referenced segment numbers
        if (segNum > 256) {
            offset += refCount * 4;
        } else {
            offset += refCount;
        }

        // Skip retention flags
        if (refCount > 0) {
            const retentionBytes = Math.floor((refCount + 7) / 8);
            offset += retentionBytes;
        }

        // Page association field size
        const pageAssocSize = (flags & 0x40) ? 1 : 4;
        offset += pageAssocSize;

        if (offset + 4 > jbig2Data.length) break;

        // Data length
        const dataLength = (jbig2Data[offset] << 24) | (jbig2Data[offset + 1] << 16) |
                          (jbig2Data[offset + 2] << 8) | jbig2Data[offset + 3];
        offset += 4;

        // Page information segment (type 48 = intermediate, 49 = end)
        if (segType === 48 || segType === 49) {
            if (offset + 8 <= jbig2Data.length) {
                width = (jbig2Data[offset] << 24) | (jbig2Data[offset + 1] << 16) |
                       (jbig2Data[offset + 2] << 8) | jbig2Data[offset + 3];
                height = (jbig2Data[offset + 4] << 24) | (jbig2Data[offset + 5] << 16) |
                        (jbig2Data[offset + 6] << 8) | jbig2Data[offset + 7];
                break;
            }
        }

        offset += dataLength;
    }

    return { width, height };
}

/**
 * Create PDF/A-1B from JBIG2 encoded pages.
 * Uses single-pass Uint8Array assembly to minimize memory usage.
 */
function createJBIG2PDF({ globalData = null, pages, metadataOptions = {} }) {
    const includeProducer = metadataOptions.includeProducer !== false;
    const includeTimestamp = metadataOptions.includeTimestamp !== false;
    if (!pages || pages.length === 0) {
        throw new Error('No pages provided');
    }

    const enc = new TextEncoder();
    const parts = [];
    let currentOffset = 0;

    function addBytes(data) {
        if (typeof data === 'string') {
            data = enc.encode(data);
        }
        parts.push(data);
        currentOffset += data.length;
    }

    // PDF header with binary marker
    addBytes('%PDF-1.4\n');
    addBytes(new Uint8Array([0x25, 0xe2, 0xe3, 0xcf, 0xd3, 0x0a]));

    const pageWidthPt = 595;
    const pageHeightPt = 842;
    const calgrayColorspace = '[/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]';

    const offsets = [];
    let objNum = 1;

    // Pre-calculate pagesObjNum so page objects can reference their parent
    const pagesObjNum = 1 + (globalData ? 1 : 0) + pages.length * 3;

    function beginObj() {
        offsets.push(currentOffset);
        const num = objNum++;
        addBytes(`${num} 0 obj\n`);
        return num;
    }

    function endObj() {
        addBytes('\nendobj\n');
    }

    // Global JBIG2 dictionary stream (if present)
    let globalObjNum = null;
    if (globalData) {
        globalObjNum = beginObj();
        addBytes(`<< /Length ${globalData.length} >>\nstream\n`);
        addBytes(globalData);
        addBytes('\nendstream');
        endObj();
    }

    const pageObjNums = [];

    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];

        // Image XObject - JBIG2Decode
        const imgObjNum = beginObj();
        const decodeParms = globalObjNum
            ? `<< /JBIG2Globals ${globalObjNum} 0 R >>`
            : '<< >>';
        addBytes(
            `<< /Type /XObject /Subtype /Image ` +
            `/Width ${page.width} /Height ${page.height} ` +
            `/ColorSpace ${calgrayColorspace} ` +
            `/BitsPerComponent 1 ` +
            `/Filter /JBIG2Decode ` +
            `/DecodeParms ${decodeParms} ` +
            `/Decode [0 1] ` +
            `/Length ${page.data.length} >>\nstream\n`
        );
        addBytes(page.data);
        addBytes('\nendstream');
        endObj();

        // Content Stream - A4 scaling and centering
        const contentObjNum = beginObj();
        const imgAspect = page.width / page.height;
        const pageAspect = pageWidthPt / pageHeightPt;
        const scale = imgAspect > pageAspect
            ? pageWidthPt / page.width
            : pageHeightPt / page.height;
        const scaledWidth = page.width * scale;
        const scaledHeight = page.height * scale;
        const xOffset = (pageWidthPt - scaledWidth) / 2;
        const yOffset = (pageHeightPt - scaledHeight) / 2;
        const contentStream = `q\n${scaledWidth.toFixed(4)} 0 0 ${scaledHeight.toFixed(4)} ${xOffset.toFixed(4)} ${yOffset.toFixed(4)} cm\n/Im${i} Do\nQ\n`;
        addBytes(`<< /Length ${contentStream.length} >>\nstream\n${contentStream}\nendstream`);
        endObj();

        // Page object
        const pageObjNum = beginObj();
        pageObjNums.push(pageObjNum);
        const rotateEntry = page.rotate ? `/Rotate ${page.rotate} ` : '';
        addBytes(
            `<< /Type /Page /Parent ${pagesObjNum} 0 R ` +
            `/MediaBox [0 0 ${pageWidthPt} ${pageHeightPt}] ` +
            rotateEntry +
            `/Resources << /XObject << /Im${i} ${imgObjNum} 0 R >> >> ` +
            `/Contents ${contentObjNum} 0 R >>`
        );
        endObj();
    }

    // Pages object
    beginObj();
    const kids = pageObjNums.map(n => `${n} 0 R`).join(' ');
    addBytes(`<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`);
    endObj();

    // XMP Metadata stream
    const metadataObjNum = beginObj();
    const timestamp = includeTimestamp
        ? new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00')
        : '1970-01-01T00:00:00+00:00';
    const creatorTool = includeProducer ? 'PDF Monochrome G4 Compressor' : '';
    const producer = includeProducer ? 'PDF Monochrome G4 Compressor' : '';
    const xmpMetadata =
        `<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n` +
        `<x:xmpmeta xmlns:x="adobe:ns:meta/">\n` +
        `  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n` +
        `    <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">\n` +
        `      <dc:format>application/pdf</dc:format>\n` +
        `    </rdf:Description>\n` +
        `    <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">\n` +
        `      <pdfaid:part>1</pdfaid:part>\n` +
        `      <pdfaid:conformance>B</pdfaid:conformance>\n` +
        `    </rdf:Description>\n` +
        `    <rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">\n` +
        `      <xmp:CreateDate>${timestamp}</xmp:CreateDate>\n` +
        `      <xmp:ModifyDate>${timestamp}</xmp:ModifyDate>\n` +
        `      <xmp:MetadataDate>${timestamp}</xmp:MetadataDate>\n` +
        `      <xmp:CreatorTool>${creatorTool}</xmp:CreatorTool>\n` +
        `    </rdf:Description>\n` +
        `    <rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">\n` +
        `      <pdf:Producer>${producer}</pdf:Producer>\n` +
        `    </rdf:Description>\n` +
        `  </rdf:RDF>\n` +
        `</x:xmpmeta>\n` +
        `<?xpacket end="w"?>`;
    const xmpBytes = enc.encode(xmpMetadata);
    addBytes(`<< /Type /Metadata /Subtype /XML /Length ${xmpBytes.length} >>\nstream\n`);
    addBytes(xmpBytes);
    addBytes('\nendstream');
    endObj();

    // OutputIntent
    const outputIntentObjNum = beginObj();
    addBytes(
        `<< /Type /OutputIntent ` +
        `/S /GTS_PDFA1 ` +
        `/OutputConditionIdentifier (Gray Gamma 2.2) ` +
        `/Info (Grayscale with Gamma 2.2) >>`
    );
    endObj();

    // Catalog
    const catalogObjNum = beginObj();
    addBytes(
        `<< /Type /Catalog /Pages ${pagesObjNum} 0 R ` +
        `/Metadata ${metadataObjNum} 0 R ` +
        `/OutputIntents [${outputIntentObjNum} 0 R] ` +
        `/MarkInfo << /Marked true >> ` +
        `/ViewerPreferences << /DisplayDocTitle true >> >>`
    );
    endObj();

    // xref table
    const xrefOffset = currentOffset;
    let xrefStr = `xref\n0 ${offsets.length + 1}\n0000000000 65535 f \n`;
    for (const offset of offsets) {
        xrefStr += `${String(offset).padStart(10, '0')} 00000 n \n`;
    }
    addBytes(xrefStr);

    // Trailer with ID array
    const idSource = `${timestamp}${pages.length}`;
    const fileId = md5(idSource).toUpperCase();
    addBytes(
        `trailer\n<< /Size ${offsets.length + 1} ` +
        `/Root ${catalogObjNum} 0 R ` +
        `/ID [<${fileId}> <${fileId}>] >>\n` +
        `startxref\n${xrefOffset}\n%%EOF\n`
    );

    // Single concatenation into final array
    const result = new Uint8Array(currentOffset);
    let pos = 0;
    for (const part of parts) {
        result.set(part, pos);
        pos += part.length;
    }
    return result;
}

/**
 * Simple hash for file ID generation (not cryptographic)
 */
function md5(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    let hex = Math.abs(hash).toString(16).padStart(8, '0');
    return (hex + hex + hex + hex).substring(0, 32);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        readJBIG2Metadata,
        createJBIG2PDF
    };
}
