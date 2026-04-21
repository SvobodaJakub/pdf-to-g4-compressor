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
 * Create a PDF from CCITT compressed pages
 * @param {Array} pages - Array of page objects {width, height, data (CCITT compressed)}
 * @param {Object} [metadataOptions] - Metadata options
 * @param {boolean} [metadataOptions.includeProducer=true] - Include Producer/CreatorTool
 * @param {boolean} [metadataOptions.includeTimestamp=true] - Include real timestamps
 * @returns {Uint8Array} PDF file data
 */
function createPDF(pages, metadataOptions) {
    const mdOpts = metadataOptions || {};
    const includeProducer = mdOpts.includeProducer !== false;
    const includeTimestamp = mdOpts.includeTimestamp !== false;
    const encoder = new TextEncoder();

    // PDF header with binary marker
    let pdf = encoder.encode("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n");

    // CalGray colorspace (PDF/A compliant)
    const calgrayColorspace = "[/CalGray << /WhitePoint [0.9505 1.0000 1.0890] /Gamma 1.0 >>]";

    const objects = [];
    let objNum = 1;

    // Reserve object number for Pages
    const pagesObjNum = objNum + (pages.length * 3); // Each page: image + content + page obj

    // Create objects for each page
    const pageObjNums = [];

    for (let i = 0; i < pages.length; i++) {
        const page = pages[i];

        // Get page dimensions (use provided dimensions or fall back to A4)
        const pageWidthPt = page.pageWidthPt || A4_WIDTH_PT;
        const pageHeightPt = page.pageHeightPt || A4_HEIGHT_PT;

        // ====================================================================
        // Image XObject
        // ====================================================================
        const imgObjNum = objNum++;
        const dataLength = page.data.length;

        const imgDict = encoder.encode(
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
            `/Length ${dataLength} >>`
        );

        const imgObj = new Uint8Array(imgDict.length + 8 + page.data.length + 10);
        let imgObjPos = 0;

        imgObj.set(imgDict, imgObjPos);
        imgObjPos += imgDict.length;

        imgObj.set(encoder.encode("\nstream\n"), imgObjPos);
        imgObjPos += 8;

        imgObj.set(page.data, imgObjPos);
        imgObjPos += page.data.length;

        imgObj.set(encoder.encode("\nendstream"), imgObjPos);

        objects.push(imgObj);

        // ====================================================================
        // Content Stream - Scale and center image on page
        // ====================================================================
        const contentObjNum = objNum++;

        // Calculate scaling
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
        const xOffset = (pageWidthPt - scaledWidth) / 2;
        const yOffset = (pageHeightPt - scaledHeight) / 2;

        const contentStream = encoder.encode(
            `q\n${scaledWidth.toFixed(4)} 0 0 ${scaledHeight.toFixed(4)} ` +
            `${xOffset.toFixed(4)} ${yOffset.toFixed(4)} cm\n/Im${i} Do\nQ\n`
        );

        const contentObj = encoder.encode(
            `<< /Length ${contentStream.length} >>`
        );

        const fullContentObj = new Uint8Array(contentObj.length + 8 + contentStream.length + 10);
        let contentObjPos = 0;

        fullContentObj.set(contentObj, contentObjPos);
        contentObjPos += contentObj.length;

        fullContentObj.set(encoder.encode("\nstream\n"), contentObjPos);
        contentObjPos += 8;

        fullContentObj.set(contentStream, contentObjPos);
        contentObjPos += contentStream.length;

        fullContentObj.set(encoder.encode("\nendstream"), contentObjPos);

        objects.push(fullContentObj);

        // ====================================================================
        // Page Object
        // ====================================================================
        const pageObjNum = objNum++;
        pageObjNums.push(pageObjNum);

        const pageObj = encoder.encode(
            `<< /Type /Page /Parent ${pagesObjNum} 0 R ` +
            `/MediaBox [0 0 ${pageWidthPt} ${pageHeightPt}] ` +
            `/Resources << /XObject << /Im${i} ${imgObjNum} 0 R >> >> ` +
            `/Contents ${contentObjNum} 0 R >>`
        );

        objects.push(pageObj);
    }

    // ========================================================================
    // Pages Object
    // ========================================================================
    objNum++; // This should equal pagesObjNum

    const kids = pageObjNums.map(n => `${n} 0 R`).join(' ');
    const pagesObj = encoder.encode(
        `<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`
    );
    objects.push(pagesObj);

    // ========================================================================
    // XMP Metadata
    // ========================================================================
    const metadataObjNum = objNum++;

    const timestamp = includeTimestamp
        ? new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00')
        : '1970-01-01T00:00:00+00:00';
    const creatorTool = includeProducer ? 'PDF Monochrome G4 Compressor' : '';
    const producer = includeProducer ? 'PDF Monochrome G4 Compressor' : '';

    const xmpMetadata = encoder.encode(
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
        `<?xpacket end="w"?>`
    );

    const metadataObj = encoder.encode(
        `<< /Type /Metadata /Subtype /XML /Length ${xmpMetadata.length} >>`
    );

    const fullMetadataObj = new Uint8Array(metadataObj.length + 8 + xmpMetadata.length + 10);
    let metadataObjPos = 0;

    fullMetadataObj.set(metadataObj, metadataObjPos);
    metadataObjPos += metadataObj.length;

    fullMetadataObj.set(encoder.encode("\nstream\n"), metadataObjPos);
    metadataObjPos += 8;

    fullMetadataObj.set(xmpMetadata, metadataObjPos);
    metadataObjPos += xmpMetadata.length;

    fullMetadataObj.set(encoder.encode("\nendstream"), metadataObjPos);

    objects.push(fullMetadataObj);

    // ========================================================================
    // OutputIntent
    // ========================================================================
    const outputIntentObjNum = objNum++;

    const outputIntentObj = encoder.encode(
        `<< /Type /OutputIntent ` +
        `/S /GTS_PDFA1 ` +
        `/OutputConditionIdentifier (Gray Gamma 2.2) ` +
        `/Info (Grayscale with Gamma 2.2) >>`
    );

    objects.push(outputIntentObj);

    // ========================================================================
    // Catalog
    // ========================================================================
    const catalogObjNum = objNum++;

    const catalogObj = encoder.encode(
        `<< /Type /Catalog /Pages ${pagesObjNum} 0 R ` +
        `/Metadata ${metadataObjNum} 0 R ` +
        `/OutputIntents [${outputIntentObjNum} 0 R] ` +
        `/MarkInfo << /Marked true >> ` +
        `/ViewerPreferences << /DisplayDocTitle true >> >>`
    );

    objects.push(catalogObj);

    // ========================================================================
    // Write objects and build xref table
    // ========================================================================
    const offsets = [];

    for (let i = 0; i < objects.length; i++) {
        offsets.push(pdf.length);

        const objHeader = encoder.encode(`${i + 1} 0 obj\n`);
        const objFooter = encoder.encode("\nendobj\n");

        const newPdf = new Uint8Array(pdf.length + objHeader.length + objects[i].length + objFooter.length);
        newPdf.set(pdf, 0);
        newPdf.set(objHeader, pdf.length);
        newPdf.set(objects[i], pdf.length + objHeader.length);
        newPdf.set(objFooter, pdf.length + objHeader.length + objects[i].length);

        pdf = newPdf;
    }

    // ========================================================================
    // Write xref table
    // ========================================================================
    const xrefOffset = pdf.length;

    let xrefTable = encoder.encode(`xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`);

    for (const offset of offsets) {
        const offsetStr = String(offset).padStart(10, '0');
        const xrefEntry = encoder.encode(`${offsetStr} 00000 n \n`);

        const newXref = new Uint8Array(xrefTable.length + xrefEntry.length);
        newXref.set(xrefTable, 0);
        newXref.set(xrefEntry, xrefTable.length);
        xrefTable = newXref;
    }

    const newPdf = new Uint8Array(pdf.length + xrefTable.length);
    newPdf.set(pdf, 0);
    newPdf.set(xrefTable, pdf.length);
    pdf = newPdf;

    // ========================================================================
    // Trailer and finish
    // ========================================================================
    const fileId = generateFileId(pages.length);

    const trailer = encoder.encode(
        `trailer\n` +
        `<< /Size ${objects.length + 1} ` +
        `/Root ${catalogObjNum} 0 R ` +
        `/ID [<${fileId}> <${fileId}>] >>\n` +
        `startxref\n${xrefOffset}\n%%EOF\n`
    );

    const finalPdf = new Uint8Array(pdf.length + trailer.length);
    finalPdf.set(pdf, 0);
    finalPdf.set(trailer, pdf.length);

    return finalPdf;
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
 * Simple hash function (poor man's MD5 for browser compatibility)
 */
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16);
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createPDF };
}
