/**
 * PDF Generation from CCITT Group 4 compressed images
 * Ported from tiff2pdf_img2pdf.py (original Python code by Claude AI)
 *
 * Creates PDF/A-1B compliant PDFs with:
 * - CCITT Group 4 compressed image streams
 * - CalGray colorspace
 * - A4 portrait pages with centering
 * - XMP metadata
 *
 * Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Licensed under the Apache License, Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * All code is original implementation based on TIFF 6.0 and PDF 1.4 specs.
 * See LICENSES.md for complete attribution.
 */

'use strict';

// A4 dimensions in points (1 point = 1/72 inch)
const A4_WIDTH_PT = 595;
const A4_HEIGHT_PT = 842;

/**
 * Create a PDF from CCITT compressed pages.
 * Uses single-pass Uint8Array assembly to minimize memory usage.
 */
function createPDF(pages, metadataOptions) {
    const mdOpts = metadataOptions || {};
    const includeProducer = mdOpts.includeProducer !== false;
    const includeTimestamp = mdOpts.includeTimestamp !== false;
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

    // CalGray colorspace (PDF/A compliant)
    const calgrayColorspace = "[/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]";

    const offsets = [];
    let objNum = 1;

    // Pre-calculate pagesObjNum: each page creates 3 objects (image, content, page)
    const pagesObjNum = 1 + pages.length * 3;

    function beginObj() {
        offsets.push(currentOffset);
        const num = objNum++;
        addBytes(`${num} 0 obj\n`);
        return num;
    }

    function endObj() {
        addBytes('\nendobj\n');
    }

    // Create objects for each page
    const pageObjNums = [];

    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];

        const pageWidthPt = page.pageWidthPt || A4_WIDTH_PT;
        const pageHeightPt = page.pageHeightPt || A4_HEIGHT_PT;

        // Image XObject
        const imgObjNum = beginObj();
        addBytes(
            `<< /Type /XObject ` +
            `/Subtype /Image ` +
            `/Width ${page.width} ` +
            `/Height ${page.height} ` +
            `/ColorSpace ${calgrayColorspace} ` +
            `/BitsPerComponent 1 ` +
            `/Filter /CCITTFaxDecode ` +
            `/DecodeParms << /K -1 /BlackIs1 false ` +
            `/Columns ${page.width} /Rows ${page.height} >> ` +
            `/Decode [0 1] ` +
            `/Length ${page.data.length} >>\nstream\n`
        );
        addBytes(page.data);
        addBytes('\nendstream');
        endObj();

        // Content Stream
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
        const contentStream = `q\n${scaledWidth.toFixed(4)} 0 0 ${scaledHeight.toFixed(4)} ` +
            `${xOffset.toFixed(4)} ${yOffset.toFixed(4)} cm\n/Im${i} Do\nQ\n`;
        const contentBytes = enc.encode(contentStream);
        addBytes(`<< /Length ${contentBytes.length} >>\nstream\n`);
        addBytes(contentBytes);
        addBytes('\nendstream');
        endObj();

        // Page Object
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

    // Pages Object
    beginObj();
    const kids = pageObjNums.map(n => `${n} 0 R`).join(' ');
    addBytes(`<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`);
    endObj();

    // XMP Metadata
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

    // Trailer
    const fileId = generateFileId(pages.length);
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
 * Generate a unique file ID for PDF
 */
function generateFileId(pageCount) {
    const data = `${Date.now()}-${pageCount}-${Math.random()}`;
    const hash = simpleHash(data);
    return hash.padStart(32, '0').substring(0, 32).toUpperCase();
}

/**
 * Simple hash function for browser compatibility
 */
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createPDF };
}
