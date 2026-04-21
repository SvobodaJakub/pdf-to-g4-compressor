#!/bin/bash
#
# Build JBIG2 WASM modules from source
#
# This script clones Leptonica and jbig2enc at known-good commits,
# applies a patch for Emscripten compatibility, and cross-compiles
# to WebAssembly.
#
# Prerequisites:
#   - Emscripten SDK (5.0.6+) installed and activated
#   - CMake 3.10+
#   - Git, Make, Python 3
#
# Usage:
#   source ~/emsdk/emsdk_env.sh
#   ./build-jbig2-wasm.sh
#
# Output:
#   jbig2.wasm and jbig2.js in the current directory (wasm/)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${HOME}/jbig2-wasm-build"

# Pinned versions
LEPTONICA_REPO="https://github.com/DanBloomberg/leptonica.git"
LEPTONICA_COMMIT="7e803e7"  # v1.84.1

JBIG2ENC_REPO="https://github.com/agl/jbig2enc.git"
JBIG2ENC_COMMIT="4cadbfe"  # latest as of 2026-04-20

# Check Emscripten is available
if ! command -v emcc &>/dev/null; then
    echo "Error: emcc not found. Run: source ~/emsdk/emsdk_env.sh"
    exit 1
fi

echo "=== Building JBIG2 WASM modules ==="
echo "Build directory: ${BUILD_DIR}"
echo "Emscripten: $(emcc --version 2>&1 | head -1)"
echo

# -----------------------------------------------------------------------
# Step 1: Clone and checkout Leptonica
# -----------------------------------------------------------------------
echo "--- Step 1: Leptonica ---"
if [ -d "${BUILD_DIR}/leptonica" ]; then
    echo "Leptonica directory exists, verifying commit..."
    cd "${BUILD_DIR}/leptonica"
    CURRENT=$(git rev-parse --short HEAD)
    if [ "$CURRENT" != "${LEPTONICA_COMMIT}" ]; then
        echo "Wrong commit ($CURRENT), re-cloning..."
        cd "${BUILD_DIR}"
        rm -rf leptonica
        git clone "${LEPTONICA_REPO}" leptonica
        cd leptonica
        git checkout "${LEPTONICA_COMMIT}"
    fi
else
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    git clone "${LEPTONICA_REPO}" leptonica
    cd leptonica
    git checkout "${LEPTONICA_COMMIT}"
fi

# Build Leptonica
mkdir -p "${BUILD_DIR}/leptonica/build-wasm"
cd "${BUILD_DIR}/leptonica/build-wasm"

emcmake cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DSW_BUILD=OFF \
  -DBUILD_PROG=OFF \
  -DENABLE_GIF=OFF \
  -DENABLE_JPEG=OFF \
  -DENABLE_PNG=OFF \
  -DENABLE_TIFF=OFF \
  -DENABLE_ZLIB=OFF \
  -DENABLE_WEBP=OFF \
  -DENABLE_OPENJPEG=OFF \
  -DCMAKE_C_FLAGS="-O3" \
  -DCMAKE_CXX_FLAGS="-O3"

emmake make -j"$(nproc)"

echo "Leptonica built: $(ls -lh src/libleptonica.a | awk '{print $5}')"

# -----------------------------------------------------------------------
# Step 2: Create include structure for jbig2enc
# -----------------------------------------------------------------------
echo "--- Step 2: Include structure ---"
mkdir -p "${BUILD_DIR}/leptonica-include/leptonica"
ln -sf "${BUILD_DIR}/leptonica/src/"*.h "${BUILD_DIR}/leptonica-include/leptonica/"
ln -sf "${BUILD_DIR}/leptonica/build-wasm/src/"*.h "${BUILD_DIR}/leptonica-include/leptonica/"

# -----------------------------------------------------------------------
# Step 3: Clone, checkout, and patch jbig2enc
# -----------------------------------------------------------------------
echo "--- Step 3: jbig2enc ---"
if [ -d "${BUILD_DIR}/jbig2enc" ]; then
    echo "jbig2enc directory exists, verifying commit..."
    cd "${BUILD_DIR}/jbig2enc"
    CURRENT=$(git rev-parse --short HEAD)
    if [ "$CURRENT" != "${JBIG2ENC_COMMIT}" ]; then
        echo "Wrong commit ($CURRENT), re-cloning..."
        cd "${BUILD_DIR}"
        rm -rf jbig2enc
        git clone "${JBIG2ENC_REPO}" jbig2enc
        cd jbig2enc
        git checkout "${JBIG2ENC_COMMIT}"
    fi
else
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    git clone "${JBIG2ENC_REPO}" jbig2enc
    cd jbig2enc
    git checkout "${JBIG2ENC_COMMIT}"
fi

# Apply Emscripten compatibility patch
# (replaces POSIX open/write/close with fopen/fwrite/fclose for MEMFS)
cd "${BUILD_DIR}/jbig2enc"
if git diff --quiet src/jbig2.cc 2>/dev/null; then
    echo "Applying Emscripten patch..."
    git apply "${SCRIPT_DIR}/jbig2enc-emscripten.patch"
else
    echo "Patch already applied (source modified)"
fi

# -----------------------------------------------------------------------
# Step 4: Build jbig2enc WASM
# -----------------------------------------------------------------------
echo "--- Step 4: Build jbig2enc WASM ---"
mkdir -p "${BUILD_DIR}/jbig2enc/build-wasm"
cd "${BUILD_DIR}/jbig2enc/build-wasm"

emcmake cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DLeptonica_DIR="${BUILD_DIR}/leptonica/build-wasm" \
  -DCMAKE_C_FLAGS="-O3 -I${BUILD_DIR}/leptonica-include" \
  -DCMAKE_CXX_FLAGS="-O3 -I${BUILD_DIR}/leptonica-include" \
  -DCMAKE_EXE_LINKER_FLAGS="-L${BUILD_DIR}/leptonica/build-wasm/src -lleptonica \
    -s FORCE_FILESYSTEM=1 \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_RUNTIME_METHODS=['FS','callMain'] \
    -s MODULARIZE=0 \
    -s EXPORT_NAME='Module' \
    -s INVOKE_RUN=0 \
    -sSTACK_SIZE=32MB"

emmake make -j"$(nproc)"

echo "jbig2.wasm: $(ls -lh jbig2.wasm | awk '{print $5}')"
echo "jbig2.js:   $(ls -lh jbig2.js | awk '{print $5}')"

# -----------------------------------------------------------------------
# Step 5: Copy to project
# -----------------------------------------------------------------------
echo "--- Step 5: Copy to project ---"
cp jbig2.wasm jbig2.js "${SCRIPT_DIR}/"

echo
echo "=== Done ==="
echo "WASM files copied to: ${SCRIPT_DIR}/"
ls -lh "${SCRIPT_DIR}/jbig2.wasm" "${SCRIPT_DIR}/jbig2.js"
