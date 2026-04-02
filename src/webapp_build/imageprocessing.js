/**
 * Image Processing Pipeline
 * Implements the GraphicsMagick pipeline:
 * - Grayscale conversion (Rec. 601 luma)
 * - Normalize (histogram stretching)
 * - Level adjustment (10%, 90%)
 * - Bilevel conversion (with/without Floyd-Steinberg dithering)
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
 * Convert RGBA canvas data to grayscale
 */
function rgbaToGrayscale(imageData) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const grayscale = new Uint8Array(width * height);

    for (let i = 0, j = 0; i < data.length; i += 4, j++) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        // Rec. 601 luma
        grayscale[j] = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
    }

    return { data: grayscale, width, height };
}

/**
 * Normalize image (histogram stretching)
 */
function normalize(image) {
    const { data, width, height } = image;
    const normalized = new Uint8Array(data.length);

    // Find min and max values
    let min = 255;
    let max = 0;

    for (let i = 0; i < data.length; i++) {
        if (data[i] < min) min = data[i];
        if (data[i] > max) max = data[i];
    }

    // Avoid division by zero
    if (max === min) {
        normalized.set(data);
        return { data: normalized, width, height };
    }

    // Stretch histogram
    const range = max - min;
    for (let i = 0; i < data.length; i++) {
        normalized[i] = Math.round(((data[i] - min) * 255) / range);
    }

    return { data: normalized, width, height };
}

/**
 * Apply level adjustment (10% black point, 90% white point)
 * This increases contrast by mapping:
 * - Values below 10% (25.5) → black (0)
 * - Values above 90% (229.5) → white (255)
 * - Values between 10%-90% → linearly scaled to 0-255
 */
function applyLevels(image, blackPercent = 10, whitePercent = 90) {
    const { data, width, height } = image;
    const adjusted = new Uint8Array(data.length);

    const blackPoint = (blackPercent / 100) * 255;
    const whitePoint = (whitePercent / 100) * 255;
    const range = whitePoint - blackPoint;

    if (range === 0) {
        adjusted.set(data);
        return { data: adjusted, width, height };
    }

    for (let i = 0; i < data.length; i++) {
        let value = data[i];

        if (value <= blackPoint) {
            adjusted[i] = 0;
        } else if (value >= whitePoint) {
            adjusted[i] = 255;
        } else {
            // Linear scaling
            adjusted[i] = Math.round(((value - blackPoint) * 255) / range);
        }
    }

    return { data: adjusted, width, height };
}

/**
 * Convert to bilevel (1-bit) without dithering
 * Uses simple thresholding at 50%
 */
function toBilevelNoDither(image, threshold = 128) {
    const { data, width, height } = image;
    const bytesPerRow = Math.ceil(width / 8);
    const bilevel = new Uint8Array(bytesPerRow * height);

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const srcIdx = y * width + x;
            const value = data[srcIdx];

            if (value < threshold) {
                // Black pixel (bit = 1 in our convention)
                const byteIdx = y * bytesPerRow + Math.floor(x / 8);
                const bitPos = 7 - (x % 8); // MSB first
                bilevel[byteIdx] |= (1 << bitPos);
            }
            // White pixel (bit = 0) - already initialized to 0
        }
    }

    return { data: bilevel, width, height };
}

/**
 * Floyd-Steinberg dithering
 * Error diffusion pattern:
 *       X   7/16
 *   3/16 5/16 1/16
 */
function toBilevelDithered(image, threshold = 128) {
    const { data, width, height } = image;
    const bytesPerRow = Math.ceil(width / 8);
    const bilevel = new Uint8Array(bytesPerRow * height);

    // Create a copy for error diffusion
    const working = new Float32Array(data);

    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            const oldPixel = working[idx];
            const newPixel = oldPixel < threshold ? 0 : 255;

            // Set bit in output
            if (newPixel === 0) {
                // Black pixel
                const byteIdx = y * bytesPerRow + Math.floor(x / 8);
                const bitPos = 7 - (x % 8);
                bilevel[byteIdx] |= (1 << bitPos);
            }

            // Calculate error
            const error = oldPixel - newPixel;

            // Distribute error to neighbors
            if (x + 1 < width) {
                working[idx + 1] += error * (7 / 16);
            }
            if (y + 1 < height) {
                if (x > 0) {
                    working[idx + width - 1] += error * (3 / 16);
                }
                working[idx + width] += error * (5 / 16);
                if (x + 1 < width) {
                    working[idx + width + 1] += error * (1 / 16);
                }
            }
        }
    }

    return { data: bilevel, width, height };
}

/**
 * Complete image processing pipeline
 * Matches cpdfgm.sh: grayscale → normalize → level 10%,90% → bilevel
 */
function processImage(imageData, options = {}) {
    const {
        dither = false,
        threshold = 128,
        blackLevel = 10,
        whiteLevel = 90
    } = options;

    // Step 1: Convert to grayscale
    let processed = rgbaToGrayscale(imageData);

    // Step 2: Normalize
    processed = normalize(processed);

    // Step 3: Level adjustment (10%, 90%)
    processed = applyLevels(processed, blackLevel, whiteLevel);

    // Step 4: Convert to bilevel
    if (dither) {
        processed = toBilevelDithered(processed, threshold);
    } else {
        processed = toBilevelNoDither(processed, threshold);
    }

    return processed;
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        rgbaToGrayscale,
        normalize,
        applyLevels,
        toBilevelNoDither,
        toBilevelDithered,
        processImage
    };
}
