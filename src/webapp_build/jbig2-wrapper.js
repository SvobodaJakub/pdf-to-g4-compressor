/**
 * JBIG2 Encoder Wrapper
 * High-level JavaScript API for the jbig2enc WASM module
 *
 * Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Licensed under Apache License 2.0
 */

class JBIG2Encoder {
    constructor() {
        this.module = null;
        this.initialized = false;
    }

    async init() {
        if (this.initialized) return;

        if (typeof window.Module === 'undefined') {
            throw new Error('jbig2.js must be loaded before initializing JBIG2Encoder');
        }

        return new Promise((resolve, reject) => {
            let checkCount = 0;
            const maxChecks = 1000;

            const checkReady = () => {
                checkCount++;

                if (window.Module &&
                    window.Module.FS &&
                    typeof window.Module.FS.mkdir === 'function' &&
                    typeof window.Module.FS.writeFile === 'function' &&
                    typeof window.Module.FS.readFile === 'function') {

                    this.module = window.Module;
                    this.initialized = true;
                    console.log('[JBIG2Encoder] WASM module initialized');
                    resolve();
                } else if (checkCount >= maxChecks) {
                    reject(new Error('JBIG2 initialization timeout'));
                } else {
                    setTimeout(checkReady, 10);
                }
            };

            checkReady();
        });
    }

    /**
     * Encode bilevel images to JBIG2 format
     * @param {Array<{width: number, height: number, data: Uint8Array}>} pages
     * @param {Object} options
     * @param {boolean} options.lossy - Use lossy compression (default: true)
     * @param {number} options.threshold - Lossy threshold 0-1 (default: 0.97)
     * @param {boolean} options.symbolCoding - Use symbol dictionary (default: true)
     * @param {Function} options.progressCallback - Progress callback(pageNum, totalPages, status)
     * @returns {Promise<{sym: Uint8Array|null, pages: Array<Uint8Array>}>}
     */
    async encode(pages, options = {}) {
        if (!this.initialized) {
            throw new Error('JBIG2Encoder not initialized. Call init() first.');
        }

        const {
            lossy = true,
            threshold = 0.97,
            symbolCoding = true,
            progressCallback = null
        } = options;

        if (!pages || pages.length === 0) {
            throw new Error('No pages provided');
        }

        const FS = this.module.FS;
        const workDir = '/jbig2_work';

        try {
            // Create work directory
            try {
                FS.mkdir(workDir);
            } catch (e) {
                this.cleanupDirectory(workDir);
                FS.mkdir(workDir);
            }

            // Convert pages to PBM and write to virtual filesystem
            if (progressCallback) progressCallback(0, pages.length, 'Converting to PBM format');

            for (let i = 0; i < pages.length; i++) {
                const page = pages[i];
                const filename = `${workDir}/page-${String(i).padStart(4, '0')}.pbm`;
                const pbm = this.createPBM(page.width, page.height, page.data);
                FS.writeFile(filename, pbm);

                if (progressCallback) {
                    progressCallback(i + 1, pages.length, 'Writing PBM files');
                }
            }

            // Build jbig2 command-line arguments
            const args = [];

            if (symbolCoding) {
                args.push('-s');
            }

            if (lossy) {
                args.push('-t');
                args.push(String(threshold));
            }

            args.push('-p');
            args.push('-b');
            args.push(`${workDir}/output`);

            for (let i = 0; i < pages.length; i++) {
                args.push(`${workDir}/page-${String(i).padStart(4, '0')}.pbm`);
            }

            if (progressCallback) {
                progressCallback(0, pages.length, 'Encoding with JBIG2');
            }

            console.log(`[JBIG2Encoder] Encoding ${pages.length} pages...`);

            const exitCode = this.module.callMain(args);

            if (exitCode !== 0) {
                throw new Error(`JBIG2 encoding failed with exit code ${exitCode}`);
            }

            if (progressCallback) {
                progressCallback(pages.length, pages.length, 'Reading output files');
            }

            // Read output files
            const result = {
                sym: null,
                pages: []
            };

            if (symbolCoding) {
                const symPath = `${workDir}/output.sym`;
                if (FS.analyzePath(symPath).exists) {
                    result.sym = FS.readFile(symPath);
                    console.log(`[JBIG2Encoder] Symbol dictionary: ${result.sym.length} bytes`);
                }
            }

            for (let i = 0; i < pages.length; i++) {
                const pagePath = `${workDir}/output.${String(i).padStart(4, '0')}`;
                if (FS.analyzePath(pagePath).exists) {
                    const pageData = FS.readFile(pagePath);
                    result.pages.push(pageData);
                } else {
                    throw new Error(`JBIG2 output file not found: ${pagePath}`);
                }
            }

            console.log(`[JBIG2Encoder] Done: sym=${result.sym ? result.sym.length : 0}B, ${result.pages.length} pages (${result.pages.reduce((a, p) => a + p.length, 0)}B total)`);

            if (progressCallback) {
                progressCallback(pages.length, pages.length, 'Complete');
            }

            return result;

        } finally {
            this.cleanupDirectory(workDir);
            try { FS.rmdir(workDir); } catch (e) {}
        }
    }

    createPBM(width, height, data) {
        const header = `P4\n${width} ${height}\n`;
        const headerBytes = new TextEncoder().encode(header);

        const pbm = new Uint8Array(headerBytes.length + data.length);
        pbm.set(headerBytes, 0);
        pbm.set(data, headerBytes.length);

        return pbm;
    }

    cleanupDirectory(dirPath) {
        if (!this.module || !this.module.FS) return;

        const FS = this.module.FS;

        try {
            const entries = FS.readdir(dirPath);
            for (const entry of entries) {
                if (entry === '.' || entry === '..') continue;

                const fullPath = `${dirPath}/${entry}`;
                try {
                    const stat = FS.stat(fullPath);
                    if (FS.isDir(stat.mode)) {
                        this.cleanupDirectory(fullPath);
                        FS.rmdir(fullPath);
                    } else {
                        FS.unlink(fullPath);
                    }
                } catch (e) {}
            }
        } catch (e) {}
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = JBIG2Encoder;
}
