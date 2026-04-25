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
        this.workDir = '/jbig2_work';
        this.pageCount = 0;
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
     * Prepare for incremental page addition.
     * Call this before addPage(), then call encode() when all pages are added.
     */
    prepareEncoding() {
        if (!this.initialized) {
            throw new Error('JBIG2Encoder not initialized. Call init() first.');
        }

        const FS = this.module.FS;

        // Aggressively clean up any leftover state from previous runs
        // (e.g., if encode() was never called after prepareEncoding due to cancellation)
        try {
            this.cleanupDirectory(this.workDir);
            try { FS.rmdir(this.workDir); } catch (e2) {}
        } catch (e) {}

        try {
            FS.mkdir(this.workDir);
        } catch (e) {
            // If mkdir still fails, try one more time with force cleanup
            try { this.cleanupDirectory(this.workDir); } catch (e2) {}
            try { FS.rmdir(this.workDir); } catch (e2) {}
            FS.mkdir(this.workDir);
        }
        this.pageCount = 0;
    }

    /**
     * Add a single page's bilevel data. Writes PBM to WASM FS immediately;
     * the caller can discard bilevelData after this returns.
     */
    addPage(width, height, bilevelData) {
        const FS = this.module.FS;
        const filename = `${this.workDir}/page-${String(this.pageCount).padStart(4, '0')}.pbm`;
        const pbm = this.createPBM(width, height, bilevelData);
        FS.writeFile(filename, pbm);
        this.pageCount++;
    }

    /**
     * Run jbig2enc on pages accumulated via addPage().
     * @param {Object} options
     * @param {boolean} options.lossy
     * @param {number} options.threshold
     * @param {boolean} options.symbolCoding
     * @param {Function} options.progressCallback
     * @returns {Promise<{sym: Uint8Array|null, pages: Array<Uint8Array>}>}
     */
    async encode(options = {}) {
        if (!this.initialized) {
            throw new Error('JBIG2Encoder not initialized.');
        }
        if (this.pageCount === 0) {
            throw new Error('No pages added. Call addPage() first.');
        }

        const {
            lossy = true,
            threshold = 0.97,
            symbolCoding = true,
            progressCallback = null
        } = options;

        const FS = this.module.FS;

        try {
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
            args.push(`${this.workDir}/output`);

            for (let i = 0; i < this.pageCount; i++) {
                args.push(`${this.workDir}/page-${String(i).padStart(4, '0')}.pbm`);
            }

            if (progressCallback) {
                progressCallback(0, this.pageCount, 'Encoding with JBIG2');
            }

            console.log(`[JBIG2Encoder] Encoding ${this.pageCount} pages...`);

            const exitCode = this.module.callMain(args);

            if (exitCode !== 0) {
                throw new Error(`JBIG2 encoding failed with exit code ${exitCode}`);
            }

            if (progressCallback) {
                progressCallback(this.pageCount, this.pageCount, 'Reading output files');
            }

            const result = {
                sym: null,
                pages: []
            };

            if (symbolCoding) {
                const symPath = `${this.workDir}/output.sym`;
                if (FS.analyzePath(symPath).exists) {
                    result.sym = FS.readFile(symPath);
                    console.log(`[JBIG2Encoder] Symbol dictionary: ${result.sym.length} bytes`);
                }
            }

            for (let i = 0; i < this.pageCount; i++) {
                const pagePath = `${this.workDir}/output.${String(i).padStart(4, '0')}`;
                if (FS.analyzePath(pagePath).exists) {
                    result.pages.push(FS.readFile(pagePath));
                } else {
                    throw new Error(`JBIG2 output file not found: ${pagePath}`);
                }
            }

            console.log(`[JBIG2Encoder] Done: sym=${result.sym ? result.sym.length : 0}B, ${result.pages.length} pages (${result.pages.reduce((a, p) => a + p.length, 0)}B total)`);

            if (progressCallback) {
                progressCallback(this.pageCount, this.pageCount, 'Complete');
            }

            return result;

        } finally {
            this.cleanupDirectory(this.workDir);
            try { FS.rmdir(this.workDir); } catch (e) {}
            this.pageCount = 0;
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
