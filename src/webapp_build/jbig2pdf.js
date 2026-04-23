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
 * Create PDF/A-1B from JBIG2 encoded pages
 * @param {Object} params
 * @param {Uint8Array|null} params.globalData - Global symbol dictionary (*.sym file)
 * @param {Array<{width: number, height: number, data: Uint8Array}>} params.pages - Page segments
 * @returns {Uint8Array} - PDF file data
 */
function createJBIG2PDF({ globalData = null, pages, metadataOptions = {} }) {
    const includeProducer = metadataOptions.includeProducer !== false;
    const includeTimestamp = metadataOptions.includeTimestamp !== false;
    if (!pages || pages.length === 0) {
        throw new Error('No pages provided');
    }

    // PDF header with binary marker
    const pdfParts = [];
    pdfParts.push('%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');

    // A4 portrait in points
    const pageWidthPt = 595;
    const pageHeightPt = 842;

    const objects = [];
    let objNum = 1;

    // CalGray color space (PDF/A compliant)
    const calgrayColorspace = '[/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]';

    // ========================================================================
    // Global JBIG2 dictionary stream (if present)
    // ========================================================================
    let globalObjNum = null;
    if (globalData) {
        globalObjNum = objNum++;

        const globalObj = `<< /Length ${globalData.length} >>\nstream\n` +
                         arrayToString(globalData) +
                         `\nendstream`;
        objects.push(globalObj);
    }

    // Create image and content objects for each page
    const pageObjNums = [];

    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];

        // ====================================================================
        // Image XObject - JBIG2Decode
        // ====================================================================
        const imgObjNum = objNum++;
        const dataLength = page.data.length;

        // Build DecodeParms
        let decodeParms;
        if (globalObjNum) {
            decodeParms = `<< /JBIG2Globals ${globalObjNum} 0 R >>`;
        } else {
            decodeParms = '<< >>';
        }

        const imgDict = `<< /Type /XObject ` +
            `/Subtype /Image ` +
            `/Width ${page.width} ` +
            `/Height ${page.height} ` +
            `/ColorSpace ${calgrayColorspace} ` +
            `/BitsPerComponent 1 ` +
            `/Filter /JBIG2Decode ` +
            `/DecodeParms ${decodeParms} ` +
            `/Decode [0 1] ` +
            `/Length ${dataLength} >>`;

        const imgObj = imgDict + '\nstream\n' + arrayToString(page.data) + '\nendstream';
        objects.push(imgObj);

        // ====================================================================
        // Content Stream - A4 scaling and centering
        // ====================================================================
        const contentObjNum = objNum++;

        // Calculate aspect ratios and scale to fit A4
        const imgAspect = page.width / page.height;
        const pageAspect = pageWidthPt / pageHeightPt;

        let scale;
        if (imgAspect > pageAspect) {
            scale = pageWidthPt / page.width;
        } else {
            scale = pageHeightPt / page.height;
        }

        const scaledWidth = page.width * scale;
        const scaledHeight = page.height * scale;

        // Center image on A4 page
        const xOffset = (pageWidthPt - scaledWidth) / 2;
        const yOffset = (pageHeightPt - scaledHeight) / 2;

        const contentStream = `q\n${scaledWidth.toFixed(4)} 0 0 ${scaledHeight.toFixed(4)} ${xOffset.toFixed(4)} ${yOffset.toFixed(4)} cm\n/Im${i} Do\nQ\n`;

        const contentObj = `<< /Length ${contentStream.length} >>\nstream\n${contentStream}\nendstream`;
        objects.push(contentObj);

        // ====================================================================
        // Page object
        // ====================================================================
        const pageObjNum = objNum++;
        pageObjNums.push(pageObjNum);

        const rotateEntry = page.rotate ? `/Rotate ${page.rotate} ` : '';
        const pageObj = `<< /Type /Page /Parent ${objNum} 0 R ` +
            `/MediaBox [0 0 ${pageWidthPt} ${pageHeightPt}] ` +
            rotateEntry +
            `/Resources << /XObject << /Im${i} ${imgObjNum} 0 R >> >> ` +
            `/Contents ${contentObjNum} 0 R >>`;
        objects.push(pageObj);
    }

    // ========================================================================
    // Pages object
    // ========================================================================
    const pagesObjNum = objNum++;

    const kids = pageObjNums.map(n => `${n} 0 R`).join(' ');
    const pagesObj = `<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`;
    objects.push(pagesObj);

    // Fix page parent references
    for (let i = 0; i < pageObjNums.length; i++) {
        const idx = pageObjNums[i] - 1;  // Object array is 0-indexed
        objects[idx] = objects[idx].replace(`/Parent ${objNum - 1} 0 R`, `/Parent ${pagesObjNum} 0 R`);
    }

    // ========================================================================
    // XMP Metadata stream - PDF/A-1B requirement
    // ========================================================================
    const metadataObjNum = objNum++;

    const timestamp = includeTimestamp
        ? new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00')
        : '1970-01-01T00:00:00+00:00';
    const creatorTool = includeProducer ? 'PDF Monochrome G4 Compressor' : '';
    const producer = includeProducer ? 'PDF Monochrome G4 Compressor' : '';

    const xmpMetadata = `<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:format>application/pdf</dc:format>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
      <pdfaid:part>1</pdfaid:part>
      <pdfaid:conformance>B</pdfaid:conformance>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
      <xmp:CreateDate>${timestamp}</xmp:CreateDate>
      <xmp:ModifyDate>${timestamp}</xmp:ModifyDate>
      <xmp:MetadataDate>${timestamp}</xmp:MetadataDate>
      <xmp:CreatorTool>${creatorTool}</xmp:CreatorTool>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
      <pdf:Producer>${producer}</pdf:Producer>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>`;

    const metadataObj = `<< /Type /Metadata /Subtype /XML /Length ${xmpMetadata.length} >>\nstream\n${xmpMetadata}\nendstream`;
    objects.push(metadataObj);

    // ========================================================================
    // OutputIntent - PDF/A-1B requirement
    // ========================================================================
    const outputIntentObjNum = objNum++;

    const outputIntentObj = `<< /Type /OutputIntent ` +
        `/S /GTS_PDFA1 ` +
        `/OutputConditionIdentifier (Gray Gamma 2.2) ` +
        `/Info (Grayscale with Gamma 2.2) >>`;
    objects.push(outputIntentObj);

    // ========================================================================
    // Catalog
    // ========================================================================
    const catalogObjNum = objNum++;

    const catalogObj = `<< /Type /Catalog /Pages ${pagesObjNum} 0 R ` +
        `/Metadata ${metadataObjNum} 0 R ` +
        `/OutputIntents [${outputIntentObjNum} 0 R] ` +
        `/MarkInfo << /Marked true >> ` +
        `/ViewerPreferences << /DisplayDocTitle true >> >>`;
    objects.push(catalogObj);

    // ========================================================================
    // Write PDF structure
    // ========================================================================
    const offsets = [];
    for (let i = 0; i < objects.length; i++) {
        offsets.push(pdfParts.join('').length);
        pdfParts.push(`${i + 1} 0 obj\n${objects[i]}\nendobj\n`);
    }

    // Write xref table
    const xrefOffset = pdfParts.join('').length;
    pdfParts.push('xref\n');
    pdfParts.push(`0 ${objects.length + 1}\n`);
    pdfParts.push('0000000000 65535 f \n');
    for (const offset of offsets) {
        pdfParts.push(`${String(offset).padStart(10, '0')} 00000 n \n`);
    }

    // ========================================================================
    // Trailer with ID array
    // ========================================================================
    // Generate file ID
    const idSource = `${timestamp}${pages.length}`;
    const fileId = md5(idSource).toUpperCase();

    pdfParts.push('trailer\n');
    pdfParts.push(`<< /Size ${objects.length + 1} ` +
                 `/Root ${catalogObjNum} 0 R ` +
                 `/ID [<${fileId}> <${fileId}>] >>\n`);
    pdfParts.push('startxref\n');
    pdfParts.push(`${xrefOffset}\n`);
    pdfParts.push('%%EOF\n');

    // Convert to Uint8Array
    return stringToArray(pdfParts.join(''));
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Convert Uint8Array to binary string (for PDF)
 * @param {Uint8Array} array
 * @returns {string}
 */
function arrayToString(array) {
    let result = '';
    for (let i = 0; i < array.length; i++) {
        result += String.fromCharCode(array[i]);
    }
    return result;
}

/**
 * Convert string to Uint8Array
 * @param {string} str
 * @returns {Uint8Array}
 */
function stringToArray(str) {
    const array = new Uint8Array(str.length);
    for (let i = 0; i < str.length; i++) {
        array[i] = str.charCodeAt(i);
    }
    return array;
}

/**
 * Simple MD5 implementation (for file ID generation)
 * @param {string} str
 * @returns {string} - Hex string
 */
function md5(str) {
    // For browser environments, we can use a simple hash
    // This doesn't need cryptographic security, just uniqueness
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }

    // Convert to hex and pad to 32 characters
    let hex = Math.abs(hash).toString(16).padStart(8, '0');
    // Duplicate to make it 32 characters (MD5-like)
    return (hex + hex + hex + hex).substring(0, 32);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        readJBIG2Metadata,
        createJBIG2PDF
    };
}
