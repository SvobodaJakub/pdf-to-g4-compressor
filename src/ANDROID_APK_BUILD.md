# Android APK Build Guide

This document explains how to build an Android APK from the PDF G4 Compressor HTML file using Google's Bubblewrap.

## Overview

**Tool**: Bubblewrap (Google's official PWA → APK converter)

**What it does**:
- Wraps the web app in an Android WebView
- Creates a Trusted Web Activity (TWA) APK
- Generates signed, publishable APK for Google Play Store
- Minimal configuration required

**Requirements**:
- Node.js 14+ and npm
- JDK 11 or newer
- Android SDK (automatically downloaded by Bubblewrap)

## Why Bubblewrap?

✅ **Official**: Made by Google Chrome team  
✅ **Simple**: Minimal configuration  
✅ **PWA-friendly**: Designed for Progressive Web Apps  
✅ **Play Store ready**: Generates signed APKs  
✅ **Active**: Well-maintained project  

## Architecture

```
pdf-to-g4-compressor.html (1.48 MB)
         ↓
   (Bubblewrap wraps it)
         ↓
    Android APK (~2-3 MB)
    ├── WebView container
    ├── HTML file (embedded or hosted)
    └── Android manifest + icons
```

**Two modes**:
1. **Hosted mode**: APK loads HTML from HTTPS URL (smaller APK)
2. **Offline mode**: APK embeds HTML file (larger APK, fully offline)

For this project: **Offline mode** (self-contained, no server needed)

## Setup Script

Create `src/setup-android-build.sh`:

```bash
#!/bin/bash
set -e

echo "Setting up Android APK build environment..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 14+ first."
    exit 1
fi

# Check Java
if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install JDK 11+ first."
    exit 1
fi

# Create build directory
BUILD_DIR="../apk-build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "Installing Bubblewrap CLI..."
npm init -y
npm install --save-dev @bubblewrap/cli

echo "Initializing Bubblewrap..."
npx bubblewrap init --manifest https://svobodajakub.github.io/manifest.json

echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit apk-build/twa-manifest.json to configure your app"
echo "2. Run: cd apk-build && npx bubblewrap build"
echo "3. Find APK in: apk-build/app-release-signed.apk"
```

## PWA Manifest

Bubblewrap needs a web app manifest. Create `manifest.json` to host alongside the HTML:

```json
{
  "name": "PDF Monochrome CCITT G4 Compressor",
  "short_name": "PDF G4 Compressor",
  "description": "Compress PDFs to monochrome CCITT Group 4 format",
  "start_url": "./pdf-to-g4-compressor.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#667eea",
  "orientation": "any",
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
}
```

**Note**: Icons can be generated from the inline SVG already in the HTML.

## Build Process

### 1. Initial Setup

```bash
cd src
chmod +x setup-android-build.sh
./setup-android-build.sh
```

This creates `../apk-build/` with Bubblewrap installed.

### 2. Configure TWA Manifest

Edit `apk-build/twa-manifest.json`:

```json
{
  "packageId": "com.svobodajakub.pdfg4compressor",
  "host": "svobodajakub.github.io",
  "name": "PDF G4 Compressor",
  "launcherName": "PDF G4",
  "display": "standalone",
  "themeColor": "#667eea",
  "backgroundColor": "#ffffff",
  "startUrl": "/pdf-to-g4-compressor.html",
  "iconUrl": "https://svobodajakub.github.io/icon-512.png",
  "maskableIconUrl": "https://svobodajakub.github.io/icon-512.png",
  "shortcuts": [],
  "enableNotifications": false,
  "isChromeOSOnly": false,
  "signingKey": {
    "path": "./android.keystore",
    "alias": "android"
  },
  "appVersion": "1",
  "appVersionCode": 1,
  "minSdkVersion": 21,
  "targetSdkVersion": 33
}
```

### 3. Build APK

```bash
cd apk-build
npx bubblewrap build
```

Bubblewrap will:
1. Download Android SDK (if needed)
2. Generate keystore (if needed)
3. Build APK
4. Sign APK

Output: `app-release-signed.apk`

### 4. Install on Device

```bash
adb install app-release-signed.apk
```

Or copy APK to device and install manually.

## Offline Mode (Embedded HTML)

To embed the HTML file in the APK instead of loading from URL:

1. Modify `twa-manifest.json`:
   ```json
   {
     "startUrl": "/offline.html",
     "fallbackType": "custom",
     "fallbackUrl": "/offline.html"
   }
   ```

2. Copy HTML to APK assets:
   ```bash
   # After bubblewrap build, before signing
   cp ../pdf-to-g4-compressor.html apk-build/app/src/main/assets/offline.html
   ```

3. Configure TWA to load from assets:
   ```java
   // In AndroidManifest.xml
   <meta-data
       android:name="asset_statements"
       android:resource="@string/asset_statements" />
   ```

**Alternative**: Use Capacitor for full offline mode (more complex but better offline support).

## Icon Generation

Generate Android icons from the inline SVG:

```bash
# Install imagemagick
sudo dnf install imagemagick  # or apt-get, brew, etc.

# Extract SVG from HTML (or recreate manually)
cat > icon.svg << 'EOF'
<svg xmlns='http://www.w3.org/2000/svg' width='512' height='512'>
  <rect width='512' height='512' fill='#667eea'/>
  <text x='256' y='256' font-family='Arial' font-size='128' 
        fill='#fff' text-anchor='middle' dominant-baseline='middle'>PDF</text>
</svg>
EOF

# Generate icons
convert icon.svg -resize 192x192 icon-192.png
convert icon.svg -resize 512x512 icon-512.png
```

## Publishing to Google Play Store

1. **Create Play Console account** ($25 one-time fee)
2. **Create app listing**
3. **Upload APK** from `apk-build/app-release-signed.apk`
4. **Configure store listing** (screenshots, description)
5. **Submit for review**

## Alternative: Capacitor (More Complex)

If Bubblewrap doesn't meet needs, consider Capacitor:

**Pros**:
- Better offline support
- Native plugins available
- More control over WebView

**Cons**:
- More complex setup
- Requires Android Studio
- Larger APK size

**Setup**:
```bash
npm install @capacitor/core @capacitor/cli
npx cap init
npx cap add android
npx cap copy
npx cap open android  # Opens Android Studio
```

## File Structure

```
project/
├── pdf-to-g4-compressor.html  # Main app (project root)
├── manifest.json              # PWA manifest (if hosting)
├── icon-192.png               # App icon
├── icon-512.png               # App icon
├── src/                       # Source code
│   ├── setup-android-build.sh # Setup script
│   └── ...
└── apk-build/                 # Android build directory (not in tarball)
    ├── package.json           # Created by setup script
    ├── node_modules/          # Bubblewrap
    ├── twa-manifest.json      # TWA configuration
    ├── android.keystore       # Signing key
    └── app-release-signed.apk # Final APK
```

## Size Estimates

- **Hosted mode**: ~2 MB APK (WebView + wrapper)
- **Offline mode**: ~3.5 MB APK (WebView + wrapper + 1.5 MB HTML)
- **Capacitor**: ~5-8 MB APK (more features, larger base)

## Testing

**On emulator**:
```bash
# Create emulator
avdmanager create avd -n test -k "system-images;android-30;google_apis;x86_64"
emulator -avd test

# Install APK
adb install app-release-signed.apk
```

**On physical device**:
1. Enable USB debugging on device
2. Connect via USB
3. `adb install app-release-signed.apk`

## Troubleshooting

**Bubblewrap init fails**:
- Check internet connection (downloads Android SDK)
- Ensure JDK 11+ is installed: `java -version`

**Build fails**:
- Check Node.js version: `node -v` (must be 14+)
- Clear cache: `rm -rf node_modules && npm install`

**APK won't install**:
- Check package name uniqueness
- Ensure device allows unknown sources
- Check Android version compatibility (minSdk 21 = Android 5.0)

**WebView blank screen**:
- Check manifest start_url is correct
- Test HTML in mobile Chrome first
- Check Chrome DevTools remote debugging

## Resources

- Bubblewrap: https://github.com/GoogleChromeLabs/bubblewrap
- TWA Guide: https://developer.chrome.com/docs/android/trusted-web-activity/
- Play Store: https://play.google.com/console

---

**Status**: Ready to implement  
**Complexity**: Medium (requires Android toolchain)  
**APK Size**: ~2-3.5 MB (depending on mode)  
**Build Time**: ~10 minutes (first time, includes SDK download)
