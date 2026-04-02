# Application Icon

## Files

- `icon.svg` - Vector source (192×192, scalable)
- `icon-192.png` - 192×192 PNG (for PWA manifest)
- `icon-512.png` - 512×512 PNG (for Android APK/Play Store)

## Design

The icon represents PDF compression:
- **Top stack**: Thick paper documents (before compression)
- **Compression arrows**: Horizontal arrows showing compression action
- **Bottom stack**: Thin compressed documents (after compression)
- **"G4" label**: References CCITT Group 4 compression
- **Purple gradient background**: Matches app UI (#667eea)

## Copyright Status

**Public Domain** - This icon was created using simple geometric shapes (rectangles, arrows, text) specifically for this project. No copyrighted or trademarked elements were used.

The design is original and does not copy or derive from any existing icons, logos, or trademarks.

## Usage

For **Bubblewrap** (Android APK):
```bash
# Use icon-512.png when prompted for icon file
bubblewrap init --manifest https://your-url/manifest.json
```

For **PWA manifest.json**:
The manifest already references the icon as base64-encoded inline SVG, but you can also use:
```json
"icons": [
  {
    "src": "icon-192.png",
    "sizes": "192x192",
    "type": "image/png"
  },
  {
    "src": "icon-512.png",
    "sizes": "512x512",
    "type": "image/png"
  }
]
```

## Regenerating PNG versions

If you modify `icon.svg`, regenerate PNGs with:

```bash
magick icon.svg -resize 192x192 icon-192.png
magick icon.svg -resize 512x512 icon-512.png
```
