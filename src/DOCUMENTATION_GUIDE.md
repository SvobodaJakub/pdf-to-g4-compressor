# Documentation Guide

This project is production-ready and distributed as a self-contained single-file HTML application.

## Quick Start

**For Users:**
- **DISTRIBUTION_GUIDE.md** - How to use the distributed HTML file
- **README.md** - Features, usage guide, quick start

**For Developers:**
- **BUILD_SUMMARY.md** - Build process and self-extracting HTML details
- **LESSONS_LEARNED.md** - CCITT G4 algorithm insights and implementation pitfalls

**For License Compliance:**
- **LICENSES.md** - Complete license texts and attributions

## Documentation Structure

### Essential Documentation

**DISTRIBUTION_GUIDE.md** (Start Here!)
- What you get in the distribution
- How to use the application
- How to extract source code
- Technical details

**README.md**
- Feature list
- Quick start guide
- Usage guide (DPI selection, dithering modes)
- Development instructions
- License summary

**BUILD_SUMMARY.md**
- Build process overview
- Self-extracting HTML implementation
- Compression details and file sizes
- How the loader works

### Developer Documentation

**LESSONS_LEARNED.md** (Essential for Maintainers!)
- CCITT G4 algorithm overview (ITU-T T.6)
- Implementation insights and pitfalls:
  - Buffer sizing for high-DPI images
  - Document replacement in browsers
  - Padding bits in non-byte-aligned widths
- Algorithm complexities explained
- Code maintenance guidelines
- Debugging strategies

**SELF_EXTRACTING_HTML.md**
- Self-extracting loader architecture
- Compression strategy
- Document replacement techniques
- Browser compatibility

**SELF_CONTAINED_DISTRIBUTION.md**
- Source embedding approach
- tar.xz compression details
- Base64 encoding strategy
- License compliance approach

**INTERNATIONALIZATION_PLAN.md**
- Multi-language support implementation
- Locale detection approach
- Translation embedding strategy
- PWA manifest localization notes

**ANDROID_APK_BUILD.md**
- Android APK build guide using Bubblewrap
- Setup requirements and process
- PWA → APK conversion workflow
- Play Store publishing steps

### Reference Documentation

**IMPLEMENTATION_SUMMARY.md**
- Architecture overview
- Module descriptions
- Testing results

**TESTING_INSTRUCTIONS.md**
- Testing procedures
- Test scenarios

**LICENSES.md**
- Complete license texts
- Third-party attributions
- Compliance information

## Project Status

✅ **Production Ready**
- Self-extracting HTML application: 1.47 MB
- Completely self-contained (includes full source code)
- Both dithered and non-dithered modes working perfectly
- Comprehensive testing completed
- PDF/A-1b compliant output

## File Size Details

| Component | Size |
|-----------|------|
| Full HTML (uncompressed) | 2.57 MB |
| Compressed with gzip | 1.12 MB |
| Final self-extracting HTML | 1.47 MB |
| **Reduction** | **40% smaller** |

The distributed HTML includes:
- Complete application code
- PDF.js renderer
- CCITT G4 encoder
- Source tarball (tar.xz + base64)
- All documentation

## For New Developers

1. **Start with DISTRIBUTION_GUIDE.md** - Learn how to extract and build
2. **Read BUILD_SUMMARY.md** - Understand the build process
3. **Study LESSONS_LEARNED.md** - Learn CCITT G4 algorithm pitfalls
4. **Review the code** - Well-commented, production-ready

## Planned Enhancements

### Internationalization (i18n)
- **Status**: Planned
- **Guide**: See `INTERNATIONALIZATION_PLAN.md`
- **Impact**: +1-2 KB, minimal
- **Languages**: English (default), Czech, German, Spanish
- **Approach**: Auto-detect browser locale, embed translations

### Android APK
- **Status**: Planned  
- **Guide**: See `ANDROID_APK_BUILD.md`
- **Tool**: Bubblewrap (Google's PWA → APK)
- **Setup**: Run `./setup-android-build.sh`
- **Output**: ~2-3 MB APK for Google Play Store

## License

Apache License 2.0 - See LICENSES.md for complete attribution and license texts.

---

**Summary:** This is a production-ready, self-contained web application distributed as a single HTML file. All source code and documentation are embedded within the file for license compliance and developer freedom.
