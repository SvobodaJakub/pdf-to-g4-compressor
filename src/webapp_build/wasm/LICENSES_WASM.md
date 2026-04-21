# WASM Module Licenses

This directory contains WebAssembly builds of open-source libraries. All licenses are compatible with the Apache License 2.0 used by this project.

---

## jbig2enc - JBIG2 Encoder

**Files**: `jbig2.wasm`, `jbig2.js` (compiled from jbig2enc)

**Copyright**: Copyright (C) 2006 Google Inc.

**Author**: Adam Langley (agl@imperialviolet.org)

**License**: Apache License 2.0

**Source Code**: https://github.com/agl/jbig2enc

**Version**: Latest (as of build date)

**License Text**:
```
Copyright (C) 2006 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## Leptonica - Image Processing Library

**Files**: Linked into `jbig2.wasm` (dependency of jbig2enc)

**Copyright**: Copyright © 2001-2020 Leptonica

**License**: BSD 2-Clause License

**Source Code**: https://github.com/DanBloomberg/leptonica

**Version**: 1.84.1

**License Text**:
```
BSD 2-Clause License

Copyright (c) 2001-2020, Leptonica
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

## Emscripten Runtime

**Files**: JavaScript runtime code in `jbig2.js`

**Copyright**: Copyright (C) 2010-2023 Emscripten authors

**License**: MIT License

**Source Code**: https://github.com/emscripten-core/emscripten

**Version**: 5.0.6 (compiler version used for build)

**License Text**:
```
MIT License

Copyright (c) 2010-2023 Emscripten authors (see AUTHORS)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Build Information

**Built on**: 2026-04-20  
**Compiler**: Emscripten 5.0.6  
**Platform**: Linux x86_64  
**Optimization**: -O3 (maximum optimization)

### Build Commands

```bash
# Leptonica
emcmake cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_*=OFF ...
emmake make

# jbig2enc  
emcmake cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS="-O3" ...
emmake make
```

See `BUILD_INSTRUCTIONS.md` for complete build procedure.

---

## License Compatibility

All three licenses (Apache-2.0, BSD-2-Clause, MIT) are:
- ✅ Compatible with each other
- ✅ Compatible with the project's Apache-2.0 license
- ✅ Permissive (allow commercial use, modification, distribution)
- ✅ Require attribution (which this file provides)

---

## Attribution Requirements

When distributing this software or derivatives:

1. **Include this LICENSES_WASM.md file** or equivalent attribution
2. **Retain copyright notices** in the source code (if distributing source)
3. **Indicate modifications** if you rebuild with changes
4. **Provide license text** for each component (as above)

---

## Source Code Access

The complete source code for all WASM components is available:

- **jbig2enc**: https://github.com/agl/jbig2enc
- **Leptonica**: https://github.com/DanBloomberg/leptonica
- **Emscripten**: https://github.com/emscripten-core/emscripten

To rebuild from source, see `BUILD_INSTRUCTIONS.md`.

---

## Patents

### JBIG2 Patents

JBIG2 is covered by patents, but this implementation **does NOT use patented performance optimizations**. We use only the patent-free features:

- ✅ Basic JBIG2 encoding (patent-free)
- ✅ Symbol extraction and dictionary (patent-free)
- ✅ Lossy compression with threshold (patent-free)
- ❌ Performance optimizations (excluded to avoid patents)

**Result**: This implementation is legal to use worldwide without patent licensing.

### Implementation Patents

Neither jbig2enc nor Leptonica asserts any implementation-specific patents that would restrict use beyond their respective open-source licenses.

---

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY.

See individual license texts above for complete warranty disclaimers.
