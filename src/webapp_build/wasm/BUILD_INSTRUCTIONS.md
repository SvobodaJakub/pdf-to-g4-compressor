# Building JBIG2 WASM Modules

## Quick Start

```bash
# Install Emscripten SDK (one-time)
cd ~
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest

# Build JBIG2 WASM
source ~/emsdk/emsdk_env.sh
cd /path/to/project/src/webapp_build/wasm
./build-jbig2-wasm.sh
```

The script clones Leptonica and jbig2enc at pinned commits, applies the
Emscripten compatibility patch, and produces `jbig2.wasm` + `jbig2.js`
in this directory.

For normal use, the pre-built WASM files are sufficient. You only need
to rebuild if updating dependencies or fixing issues.

## What the Build Does

1. Clones **Leptonica** 1.84.1 (`7e803e7`) and builds a static library
   with all image format support disabled (only PBM needed)
2. Clones **jbig2enc** (`4cadbfe`) and applies `jbig2enc-emscripten.patch`
3. Cross-compiles jbig2enc to WebAssembly with Emscripten

## Files

| File | Purpose |
|------|---------|
| `build-jbig2-wasm.sh` | Automated build script |
| `jbig2enc-emscripten.patch` | Patch for MEMFS file I/O compatibility |
| `jbig2.wasm` | Pre-built WebAssembly binary (~319KB) |
| `jbig2.js` | Pre-built Emscripten JS loader (~68KB) |
| `LICENSES_WASM.md` | License information for bundled code |

## The Emscripten Patch

jbig2enc uses POSIX `open()`/`write()`/`close()` for file output. These
low-level syscalls don't work correctly with Emscripten's MEMFS virtual
filesystem. The patch replaces them with `fopen()`/`fwrite()`/`fclose()`,
which Emscripten handles properly.

## Key Build Flags

| Flag | Purpose |
|------|---------|
| `-s FORCE_FILESYSTEM=1` | Enable MEMFS virtual filesystem |
| `-s ALLOW_MEMORY_GROWTH=1` | Dynamic WASM memory allocation |
| `-s EXPORTED_RUNTIME_METHODS=['FS','callMain']` | JS access to filesystem and main() |
| `-s MODULARIZE=0 -s EXPORT_NAME='Module'` | Global `Module` object |
| `-s INVOKE_RUN=0` | Don't auto-run main() |
| `-sSTACK_SIZE=32MB` | Large stack for processing full-page images |

## Prerequisites

- **Emscripten SDK** 5.0.6+ (https://emscripten.org/)
- **CMake** 3.10+, **Git**, **Make**, **Python 3**
- Linux or macOS (Windows via WSL)

## Troubleshooting

- **"emcc: command not found"** - Run `source ~/emsdk/emsdk_env.sh`
- **Header not found errors** - The script creates symlinks; re-run from scratch
- **WASM > 1MB** - Ensure `-DCMAKE_BUILD_TYPE=Release` (debug builds are larger)
- **Stack overflow at runtime** - Increase `-sSTACK_SIZE`

## Version Information

- **Emscripten**: 5.0.6
- **Leptonica**: 1.84.1 (commit `7e803e7`)
- **jbig2enc**: commit `4cadbfe`

## Licenses

- **jbig2enc**: Apache 2.0
- **Leptonica**: BSD 2-Clause
- **Emscripten runtime**: MIT

See `LICENSES_WASM.md` for full text.
