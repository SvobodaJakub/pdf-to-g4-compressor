# Android APK Build Guide

This guide covers building a **fully offline Android APK** with the HTML file embedded and **NO internet permission**.

## What You Get

- ✅ Pure Android WebView wrapper (~100 lines of code)
- ✅ **NO internet permission** in manifest
- ✅ Fully offline - HTML embedded in APK assets
- ✅ No Node.js, npm, Capacitor, or Bubblewrap
- ✅ Just Java + Gradle + Android SDK
- ✅ APK size: ~3.7 MB (includes 1.65 MB HTML)

## Prerequisites

Install Java 17+:

```bash
# Fedora/RHEL
sudo dnf install java-17-openjdk java-17-openjdk-devel

# Ubuntu/Debian
sudo apt install openjdk-17-jdk

# Verify
java -version  # Should show 17 or higher
```

Optional (for icons):
```bash
# Fedora/RHEL
sudo dnf install ImageMagick

# Ubuntu/Debian
sudo apt install imagemagick
```

## Quick Start

### 1. Build the APK Structure

```bash
cd src
./build-apk.sh
```

This creates `../android-build/` (at project root) with complete Android project.

**First time:** Gradle will download Android SDK (~500 MB) - be patient!

### 2. Create Signing Key (One-Time)

```bash
cd ..  # Go to project root
mkdir -p android-private

keytool -genkey -v -keystore android-private/release.keystore \
        -alias pdf-g4-key -keyalg RSA -keysize 2048 -validity 10000
```

**You'll be asked:**
- Keystore password (remember this!)
- Your name
- Organization unit (optional, can skip)
- Organization (optional, can skip)
- City, State, Country (optional, can skip)

**IMPORTANT:** Save the password! You'll need it every time you build.

### 3. Create Keystore Properties

```bash
# Still in project root
cat > android-private/keystore.properties << 'EOF'
storeFile=android-private/release.keystore
storePassword=YOUR_PASSWORD_HERE
keyAlias=pdf-g4-key
keyPassword=YOUR_PASSWORD_HERE
EOF
```

Replace `YOUR_PASSWORD_HERE` with the password you set above.

### 4. Build the APK

```bash
cd android-build/
./gradlew assembleRelease
```

**First build:** 5-10 minutes (downloads dependencies)  
**Subsequent builds:** 30-60 seconds

### 5. Find Your APK

```
android-build/app/build/outputs/apk/release/app-release.apk
```

Done! This APK is signed and ready for Play Store or sideloading.

## Install on Device

**Via USB (adb):**
```bash
adb install app/build/outputs/apk/release/app-release.apk
```

**Via file copy:**
- Copy APK to phone
- Tap to install
- Allow "Install from unknown sources" if prompted

## What's Inside the APK

```
app-release.apk (~3.7 MB)
├── AndroidManifest.xml (NO internet permission!)
├── MainActivity.java (WebView wrapper)
├── assets/
│   └── index.html (1.65 MB - your HTML with embedded tarball!)
└── res/
    └── mipmap-*/
        └── ic_launcher.png (your icon in various sizes)
```

## The Code (Total: ~100 lines)

**AndroidManifest.xml** - No internet permission:
```xml
<manifest package="com.svobodajakub.pdfg4compressor">
    <!-- NO INTERNET PERMISSION -->
    <application ...>
        <activity android:name=".MainActivity" .../>
    </application>
</manifest>
```

**MainActivity.java** - Just loads HTML:
```java
WebView webView = new WebView(this);
webView.getSettings().setJavaScriptEnabled(true);
webView.loadUrl("file:///android_asset/index.html");
setContentView(webView);
```

That's it!

## Updating the APK

When you update the HTML file:

```bash
cd src
./build-apk.sh  # Answer 'y' to clean build directory
# Follow steps 4-5 again (reuse existing keystore)
```

**Important:** Increment version numbers in `app/build.gradle`:
```gradle
versionCode 2      // Increment by 1
versionName "1.1"  // Update as needed
```

## Google Play Store Publishing

### Create Play Console Account

1. Go to: https://play.google.com/console
2. Pay $25 one-time fee
3. Verify identity (takes 1-2 days)

### Upload APK

1. **Create app**
   - App name: "PDF G4 Compressor"
   - Default language: English
   - App type: App
   - Free/Paid: Free

2. **Set up app content**
   - Privacy Policy URL: `https://github.com/SvobodaJakub/pdf-to-g4-compressor/blob/main/src/privacy_policy.md`
   - Data Safety: "No data collected"
   - Target age: All ages
   - Content rating: Fill questionnaire → will be "Everyone"

3. **Upload APK**
   - Production → Create release
   - Upload `app-release.apk`
   - Release notes: "Initial release"

4. **Store listing**
   - Short description: "Compress PDFs to monochrome CCITT G4 format offline"
   - Full description:
     ```
     Compress PDF files to highly efficient monochrome CCITT Group 4 format.
     
     FEATURES
     • Compress PDFs by 90%+ with bilevel conversion
     • CCITT Group 4 compression (ITU-T T.6)
     • Dithered or sharp output modes
     • Custom DPI settings (72-1200)
     • 100% offline - no internet required
     • No data collection or tracking
     • Open source
     
     PERFECT FOR
     • Scanned documents
     • Text documents
     • Forms and receipts
     • Black and white images
     
     Works completely offline. Your files never leave your device.
     ```
   - App icon: Upload `icon-512.png`
   - Screenshots: Take 2-8 on device (required)
   - Category: Productivity

5. **Submit for review**
   - Review takes 1-7 days
   - You'll receive email when approved

### Update Policy

**Annual requirement:** Update targetSdk to latest within 12 months of new Android release.

**To update targetSdk** (takes 5 minutes):
1. Edit `app/build.gradle`:
   ```gradle
   targetSdk 35  // Update this number
   versionCode 2  // Increment
   ```
2. Rebuild APK
3. Upload to Play Console

**No other updates required!** App can stay published indefinitely with annual targetSdk bump.

## Troubleshooting

### "JAVA_HOME not set"
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

### "Android SDK not found"
First Gradle build downloads it automatically. Wait for download to complete.

### "Gradle build failed"
```bash
cd android-build
./gradlew clean
./gradlew assembleRelease
```

### "Signing failed"
Check `android-private/keystore.properties` has correct password and paths.

### "APK won't install"
- Enable "Install from unknown sources" in Android settings
- Check Android version (requires 5.0+)

### "WebView shows blank screen"
- Open Chrome DevTools remote debugging
- Check console for JavaScript errors
- Test HTML file in mobile Chrome browser first

## File Structure

```
project-root/
├── src/
│   ├── build-apk.sh              # Build script
│   ├── icon.svg                  # Source icon
│   └── icon-512.png              # For Play Store
├── android-build/                # Generated by build-apk.sh (gitignored)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml
│   │   │   ├── java/.../MainActivity.java
│   │   │   ├── assets/index.html (your HTML)
│   │   │   └── res/mipmap-*/ic_launcher.png
│   │   └── build.gradle
│   └── gradlew
└── android-private/              # Signing keys (BACKUP, don't commit to git!)
    ├── release.keystore          # YOUR SIGNING KEY - BACKUP THIS!
    └── keystore.properties       # Passwords
```

## Important Files to Backup

**CRITICAL - Backup these:**
- `android-private/release.keystore` - You CANNOT publish updates without this!
- `android-private/keystore.properties` - Contains passwords

**Loss of keystore = cannot update app on Play Store!**

Store backups securely (password manager, encrypted backup, etc.)

**DO NOT commit android-private/ to git!** Add to .gitignore.

## Resources

- Android Developer Guide: https://developer.android.com/guide
- Play Console Help: https://support.google.com/googleplay/android-developer
- WebView Documentation: https://developer.android.com/reference/android/webkit/WebView

---

**Questions?** Open an issue: https://github.com/SvobodaJakub/pdf-to-g4-compressor/issues
