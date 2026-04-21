#!/bin/bash
set -e

echo "========================================="
echo "PDF G4 Compressor - Android APK Builder"
echo "========================================="
echo ""

# Get script directory (works regardless of where script is called from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SRC_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/android-build"
KEYSTORE_DIR="$PROJECT_ROOT/android-private"

# ============================================================================
# VERSION CONFIGURATION
# ============================================================================
# Increment these for each Google Play release:
#   versionCode: Integer, must increase with each release (1, 2, 3, ...)
#   versionName: User-visible version string (e.g., "1.0", "1.1.0", "2.0")
VERSION_CODE=10
VERSION_NAME="1.2.0"

echo "Script directory: $SCRIPT_DIR"
echo "Source directory: $SRC_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Build directory: $BUILD_DIR"
echo "Version: $VERSION_NAME (code $VERSION_CODE)"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install JDK 17+ first."
    echo "   Fedora: sudo dnf install java-17-openjdk java-17-openjdk-devel"
    exit 1
fi

echo "✓ Java $(java -version 2>&1 | head -1)"
echo ""

# Find HTML file
HTML_FILE="$PROJECT_ROOT/pdf-to-g4-compressor.html"
if [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML file not found at: $HTML_FILE"
    echo "Please build the HTML file first (run build.py)"
    exit 1
fi
echo "✓ Found HTML file: $HTML_FILE"
echo ""

# Create build directory
if [ -d "$BUILD_DIR" ]; then
    echo "⚠ Build directory exists. Clean it? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        rm -rf "$BUILD_DIR"
    else
        echo "Using existing build directory..."
    fi
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "Creating Android project structure..."

# Create directory structure
mkdir -p app/src/main/java/com/svobodajakub/pdfg4compressor
mkdir -p app/src/main/res/drawable
mkdir -p app/src/main/res/mipmap-hdpi
mkdir -p app/src/main/res/mipmap-mdpi
mkdir -p app/src/main/res/mipmap-xhdpi
mkdir -p app/src/main/res/mipmap-xxhdpi
mkdir -p app/src/main/res/mipmap-xxxhdpi
mkdir -p app/src/main/res/values
mkdir -p app/src/main/assets

# Copy HTML file
echo "Copying HTML file..."
cp "$HTML_FILE" app/src/main/assets/index.html
echo "✓ Copied $(du -h app/src/main/assets/index.html | cut -f1) HTML file"
echo ""

# Generate icons from SVG
echo "Generating Android icons..."
if command -v magick &> /dev/null || command -v convert &> /dev/null; then
    CONVERT_CMD="magick"
    if ! command -v magick &> /dev/null; then
        CONVERT_CMD="convert"
    fi

    ICON_SVG="$SRC_DIR/icon.svg"
    if [ -f "$ICON_SVG" ]; then
        $CONVERT_CMD "$ICON_SVG" -resize 48x48 app/src/main/res/mipmap-mdpi/ic_launcher.png
        $CONVERT_CMD "$ICON_SVG" -resize 72x72 app/src/main/res/mipmap-hdpi/ic_launcher.png
        $CONVERT_CMD "$ICON_SVG" -resize 96x96 app/src/main/res/mipmap-xhdpi/ic_launcher.png
        $CONVERT_CMD "$ICON_SVG" -resize 144x144 app/src/main/res/mipmap-xxhdpi/ic_launcher.png
        $CONVERT_CMD "$ICON_SVG" -resize 192x192 app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
        echo "✓ Generated launcher icons"
    else
        echo "⚠ Icon SVG not found, using placeholder icons"
    fi
else
    echo "⚠ ImageMagick not found (install: sudo dnf install ImageMagick)"
    echo "⚠ Skipping icon generation - APK will use default icons"
fi
echo ""

# Create source files (these are generated, not hardcoded paths)
cat > "app/src/main/AndroidManifest.xml" << 'MANIFEST_EOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- NO INTERNET PERMISSION - Fully offline app -->

    <application
        android:allowBackup="false"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:theme="@style/AppTheme"
        android:hardwareAccelerated="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
MANIFEST_EOF

cat > "app/src/main/java/com/svobodajakub/pdfg4compressor/MainActivity.java" << 'JAVA_EOF'
package com.svobodajakub.pdfg4compressor;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.WindowManager;
import android.widget.Toast;
import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

import java.io.OutputStream;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public class MainActivity extends ComponentActivity {
    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;

    private ActivityResultLauncher<Intent> fileChooserLauncher;
    private ActivityResultLauncher<Intent> fileSaverLauncher;

    private String pendingFilename;
    private byte[] pendingFileData;
    private String pendingMimeType;

    // Track modal state
    private volatile boolean modalIsOpen = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Keep screen on during PDF processing
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // Register activity result launchers (replaces deprecated startActivityForResult)
        fileChooserLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (filePathCallback != null) {
                    Uri[] results = null;
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        String dataString = result.getData().getDataString();
                        if (dataString != null) {
                            results = new Uri[]{Uri.parse(dataString)};
                        }
                    }
                    filePathCallback.onReceiveValue(results);
                    filePathCallback = null;
                }
            }
        );

        fileSaverLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri uri = result.getData().getData();
                    if (uri != null) {
                        try {
                            OutputStream outputStream = getContentResolver().openOutputStream(uri);
                            if (outputStream != null) {
                                outputStream.write(pendingFileData);
                                outputStream.close();
                                Toast.makeText(this, "File saved: " + pendingFilename,
                                    Toast.LENGTH_SHORT).show();
                            }
                        } catch (Exception e) {
                            Toast.makeText(this, "Error saving file: " + e.getMessage(),
                                Toast.LENGTH_SHORT).show();
                        } finally {
                            pendingFileData = null;
                            pendingFilename = null;
                            pendingMimeType = null;
                        }
                    }
                }
            }
        );

        // Create WebView
        webView = new WebView(this);
        setContentView(webView);

        // Configure WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setDatabaseEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        // Enable zoom controls (useful for PDF preview)
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        // Custom WebViewClient to handle external links
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();

                // Open external URLs (http/https) in system browser
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(intent);
                    } catch (Exception e) {
                        Toast.makeText(MainActivity.this, "Cannot open browser", Toast.LENGTH_SHORT).show();
                    }
                    return true;
                }

                // Allow file:// URLs to load in WebView
                return false;
            }
        });

        // Custom WebChromeClient to handle file picker
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback,
                                            FileChooserParams fileChooserParams) {
                // Store callback for later use
                MainActivity.this.filePathCallback = filePathCallback;

                // Create file chooser intent (accept PDF and ZIP files)
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.setType("*/*");
                String[] mimeTypes = {"application/pdf", "application/zip"};
                intent.putExtra(Intent.EXTRA_MIME_TYPES, mimeTypes);
                intent.addCategory(Intent.CATEGORY_OPENABLE);

                try {
                    fileChooserLauncher.launch(Intent.createChooser(intent, "Select file"));
                } catch (Exception e) {
                    filePathCallback.onReceiveValue(null);
                    MainActivity.this.filePathCallback = null;
                    Toast.makeText(MainActivity.this, "Cannot open file picker", Toast.LENGTH_SHORT).show();
                    return false;
                }

                return true;
            }
        });

        // Add JavaScript interface for file saving and modal state tracking
        webView.addJavascriptInterface(new FileHandler(), "AndroidFileHandler");
        webView.addJavascriptInterface(new ModalStateHandler(), "AndroidModalState");

        // Handle back button to close modals first
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (modalIsOpen) {
                    // Close the modal via JavaScript (using classList, not style.display)
                    webView.evaluateJavascript(
                        "(function() {" +
                            "var aboutModal = document.getElementById('aboutModal');" +
                            "var licenseModal = document.getElementById('licenseModal');" +
                            "var languageModal = document.getElementById('languageModal');" +
                            "if (aboutModal && aboutModal.classList.contains('show')) {" +
                                "aboutModal.classList.remove('show');" +
                            "}" +
                            "if (licenseModal && licenseModal.classList.contains('show')) {" +
                                "licenseModal.classList.remove('show');" +
                            "}" +
                            "if (languageModal && languageModal.classList.contains('show')) {" +
                                "languageModal.classList.remove('show');" +
                            "}" +
                        "})()",
                        null
                    );
                    modalIsOpen = false;
                    // Stay in app, don't exit
                } else if (webView.canGoBack()) {
                    // Navigate back in WebView history
                    webView.goBack();
                } else {
                    // Exit app
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });

        // Load HTML from assets
        webView.loadUrl("file:///android_asset/index.html");
    }

    // JavaScript interface for file operations
    public class FileHandler {
        @JavascriptInterface
        public void saveFile(String filename, String base64Data, String mimeType) {
            runOnUiThread(() -> {
                try {
                    // Decode base64 data
                    pendingFileData = Base64.decode(base64Data, Base64.DEFAULT);
                    pendingFilename = filename;
                    pendingMimeType = mimeType;

                    // Create file save intent
                    Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType(mimeType);
                    intent.putExtra(Intent.EXTRA_TITLE, filename);

                    // Suggest Downloads directory
                    intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI,
                        Uri.parse("content://com.android.externalstorage.documents/document/primary:Download"));

                    fileSaverLauncher.launch(intent);
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this, "Error preparing file: " + e.getMessage(),
                        Toast.LENGTH_SHORT).show();
                }
            });
        }
    }

    // JavaScript interface for modal state tracking
    public class ModalStateHandler {
        @JavascriptInterface
        public void setModalOpen(boolean isOpen) {
            modalIsOpen = isOpen;
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
JAVA_EOF

cat > "app/src/main/res/values/strings.xml" << 'STRINGS_EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">PDF G4 Compressor</string>
</resources>
STRINGS_EOF

cat > "app/src/main/res/values/styles.xml" << 'STYLES_EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Explicit Light theme so WebView sets prefers-color-scheme:light -->
    <style name="AppTheme" parent="@android:style/Theme.DeviceDefault.Light.NoActionBar">
        <item name="android:statusBarColor">#000000</item>
        <item name="android:windowLightStatusBar">false</item>
    </style>
</resources>
STYLES_EOF

# Dark mode theme variant (values-night/) — used when system is in dark mode
mkdir -p "app/src/main/res/values-night"
cat > "app/src/main/res/values-night/styles.xml" << 'STYLES_NIGHT_EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Dark theme so WebView sets prefers-color-scheme:dark -->
    <style name="AppTheme" parent="@android:style/Theme.DeviceDefault.NoActionBar">
        <item name="android:statusBarColor">#000000</item>
        <item name="android:windowLightStatusBar">false</item>
    </style>
</resources>
STYLES_NIGHT_EOF

# Create Android 15 (API 35) specific theme to opt out of edge-to-edge
mkdir -p "app/src/main/res/values-v35"
cat > "app/src/main/res/values-v35/styles.xml" << 'STYLES_V35_EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="@android:style/Theme.DeviceDefault.Light.NoActionBar">
        <item name="android:windowOptOutEdgeToEdgeEnforcement">true</item>
    </style>
</resources>
STYLES_V35_EOF

# Dark mode variant for API 35
mkdir -p "app/src/main/res/values-night-v35"
cat > "app/src/main/res/values-night-v35/styles.xml" << 'STYLES_NIGHT_V35_EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="@android:style/Theme.DeviceDefault.NoActionBar">
        <item name="android:windowOptOutEdgeToEdgeEnforcement">true</item>
    </style>
</resources>
STYLES_NIGHT_V35_EOF

# Create root build.gradle
cat > "build.gradle" << 'GRADLE_EOF'
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.3.0'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
GRADLE_EOF

# Create app build.gradle
cat > "app/build.gradle" << APP_GRADLE_EOF
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.svobodajakub.pdfg4compressor'
    compileSdk 35

    defaultConfig {
        applicationId "com.svobodajakub.pdfg4compressor"
        minSdk 21
        targetSdk 35
        versionCode $VERSION_CODE
        versionName "$VERSION_NAME"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt')
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }

    // Signing configuration (if keystore exists)
    def keystorePropertiesFile = rootProject.file("../android-private/keystore.properties")
    if (keystorePropertiesFile.exists()) {
        def keystoreProperties = new Properties()
        keystoreProperties.load(new FileInputStream(keystorePropertiesFile))

        signingConfigs {
            release {
                storeFile rootProject.file("../" + keystoreProperties['storeFile'])
                storePassword keystoreProperties['storePassword']
                keyAlias keystoreProperties['keyAlias']
                keyPassword keystoreProperties['keyPassword']
            }
        }

        buildTypes {
            release {
                signingConfig signingConfigs.release
            }
        }
    }
}

dependencies {
    implementation 'androidx.webkit:webkit:1.7.0'
    implementation 'androidx.activity:activity:1.9.0'
    implementation 'androidx.core:core:1.13.0'

    // Force consistent Kotlin version to avoid duplicate class errors
    constraints {
        implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.0") {
            because("Resolve Kotlin stdlib version conflicts")
        }
    }
}
APP_GRADLE_EOF

# Create settings.gradle
cat > "settings.gradle" << 'SETTINGS_EOF'
include ':app'
SETTINGS_EOF

# Create gradle.properties
cat > "gradle.properties" << 'PROPS_EOF'
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
android.enableJetifier=true
PROPS_EOF

# Create local.properties with Android SDK path
# Try common locations: ~/Android, $ANDROID_HOME, $ANDROID_SDK_ROOT
ANDROID_SDK_PATH=""
if [ -d "$HOME/Android/platform-tools" ]; then
    ANDROID_SDK_PATH="$HOME/Android"
elif [ -n "$ANDROID_HOME" ] && [ -d "$ANDROID_HOME" ]; then
    ANDROID_SDK_PATH="$ANDROID_HOME"
elif [ -n "$ANDROID_SDK_ROOT" ] && [ -d "$ANDROID_SDK_ROOT" ]; then
    ANDROID_SDK_PATH="$ANDROID_SDK_ROOT"
elif [ -d "/usr/lib/android-sdk" ]; then
    ANDROID_SDK_PATH="/usr/lib/android-sdk"
fi

if [ -n "$ANDROID_SDK_PATH" ]; then
    cat > "local.properties" << EOF
sdk.dir=$ANDROID_SDK_PATH
EOF
    echo "✓ Android SDK found at: $ANDROID_SDK_PATH"
else
    echo "⚠ Warning: Android SDK not found. Please set ANDROID_HOME or install Android SDK to ~/Android"
    echo "  You may need to create local.properties manually with: sdk.dir=/path/to/android/sdk"
fi

# Create gradle wrapper
mkdir -p gradle/wrapper
cat > "gradle/wrapper/gradle-wrapper.properties" << 'WRAPPER_EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.7-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
WRAPPER_EOF

# Download gradle wrapper if not present
if [ ! -f "gradlew" ]; then
    echo "Downloading Gradle wrapper..."
    curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradle/wrapper/gradle-wrapper.jar -o gradle/wrapper/gradle-wrapper.jar
    curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradlew -o gradlew
    curl -L https://raw.githubusercontent.com/gradle/gradle/master/gradlew.bat -o gradlew.bat
    chmod +x gradlew
fi

# Create emulator setup and screenshot scripts
echo "Creating emulator setup scripts for Google Play screenshots..."

cat > "setup-emulators.sh" << 'SETUP_EOF'
#!/bin/bash
set -e

echo "========================================="
echo "Android Emulator Setup for Screenshots"
echo "========================================="
echo ""

# Check if ANDROID_HOME is set
if [ -z "$ANDROID_HOME" ]; then
    echo "⚠ ANDROID_HOME not set. Trying default location..."
    export ANDROID_HOME="$HOME/Android"
fi

if [ ! -d "$ANDROID_HOME" ]; then
    echo "❌ Android SDK not found at: $ANDROID_HOME"
    echo ""
    echo "Please install Android SDK first:"
    echo "  mkdir -p ~/Android/cmdline-tools"
    echo "  cd ~/Android/cmdline-tools"
    echo "  wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
    echo "  unzip commandlinetools-linux-11076708_latest.zip"
    echo "  mv cmdline-tools latest"
    echo ""
    echo "Then run:"
    echo "  export ANDROID_HOME=~/Android"
    echo "  export PATH=\$ANDROID_HOME/cmdline-tools/latest/bin:\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/emulator:\$PATH"
    echo "  yes | sdkmanager --licenses"
    echo "  sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' 'emulator' 'system-images;android-34;google_apis;x86_64'"
    exit 1
fi

# Set up PATH
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

# Check for required tools
if ! command -v avdmanager &> /dev/null; then
    echo "❌ avdmanager not found. Please install Android SDK command-line tools."
    exit 1
fi

if ! command -v sdkmanager &> /dev/null; then
    echo "❌ sdkmanager not found. Please install Android SDK command-line tools."
    exit 1
fi

echo "✓ Android SDK found at: $ANDROID_HOME"
echo ""

# Check if system image is installed
SYSTEM_IMAGE="system-images;android-34;google_apis;x86_64"
echo "Checking for system image: $SYSTEM_IMAGE"

if ! sdkmanager --list_installed | grep -q "$SYSTEM_IMAGE"; then
    echo "⚠ System image not installed. Installing..."
    echo "This will download ~500MB and may take 5-10 minutes."
    echo ""
    sdkmanager "$SYSTEM_IMAGE"
    echo "✓ System image installed"
else
    echo "✓ System image already installed"
fi
echo ""

# Function to create AVD
create_avd() {
    local name=$1
    local device=$2
    local tag=$3

    echo "Creating AVD: $name"

    # Delete existing AVD if it exists
    if avdmanager list avd | grep -q "Name: $name"; then
        echo "  Deleting existing AVD..."
        avdmanager delete avd -n "$name" || true
    fi

    # Create new AVD
    echo "no" | avdmanager create avd \
        --name "$name" \
        --package "$SYSTEM_IMAGE" \
        --device "$device" \
        --tag "google_apis" \
        --abi "x86_64"

    # Configure AVD
    local avd_dir="$HOME/.android/avd/${name}.avd"
    if [ -f "$avd_dir/config.ini" ]; then
        # Enable hardware acceleration
        echo "hw.gpu.enabled=yes" >> "$avd_dir/config.ini"
        echo "hw.gpu.mode=auto" >> "$avd_dir/config.ini"
        # Set RAM
        echo "hw.ramSize=2048" >> "$avd_dir/config.ini"
        # Enable keyboard
        echo "hw.keyboard=yes" >> "$avd_dir/config.ini"
    fi

    echo "✓ Created: $name ($device)"
    echo ""
}

echo "========================================="
echo "Creating Android Virtual Devices (AVDs)"
echo "========================================="
echo ""

# List available devices
echo "Available device definitions:"
avdmanager list device | grep "id:" | head -20
echo ""

# Create three AVDs for Google Play Store screenshot requirements
echo "Creating 3 AVDs for screenshots..."
echo ""

# 1. Phone (required)
# Using Pixel 6 - 6.4" display, 1080x2400, 411 DPI
create_avd "screenshot_phone" "pixel_6" "google_apis"

# 2. 7-inch tablet (required)
# Using Nexus 7 - 7" display, 800x1280, 213 DPI
create_avd "screenshot_tablet_7" "Nexus 7" "google_apis"

# 3. 10-inch tablet (required)
# Using Pixel Tablet - 10.95" display, 1600x2560, 280 DPI
create_avd "screenshot_tablet_10" "pixel_tablet" "google_apis"

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Created AVDs:"
avdmanager list avd | grep "Name:"
echo ""
echo "To run emulators, use the provided run scripts:"
echo "  ./run-emulator-phone.sh       # Phone (Pixel 6)"
echo "  ./run-emulator-tablet-7.sh    # 7-inch tablet (Nexus 7)"
echo "  ./run-emulator-tablet-10.sh   # 10-inch tablet (Pixel Tablet)"
echo ""
echo "Each script will:"
echo "  1. Start the emulator"
echo "  2. Wait for boot to complete"
echo "  3. Install the APK"
echo "  4. Push example PDF to Downloads folder"
echo "  5. Print instructions for taking screenshots"
echo ""
echo "To change language/locale in emulator:"
echo "  Use: ./change-locale.sh de-DE"
echo "  Or manually: Settings → System → Languages & input → Languages"
echo ""
SETUP_EOF

cat > "run-emulator-phone.sh" << 'PHONE_EOF'
#!/bin/bash
set -e

echo "========================================="
echo "Screenshot Emulator - Phone (Pixel 6)"
echo "========================================="
echo ""

# Setup environment
if [ -z "$ANDROID_HOME" ]; then
    export ANDROID_HOME="$HOME/Android"
fi
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

# Configuration
AVD_NAME="screenshot_phone"
APK_PATH="app/build/outputs/apk/release/app-release.apk"
EXAMPLE_PDF="../example document.pdf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Check if AVD exists
if ! avdmanager list avd | grep -q "Name: $AVD_NAME"; then
    echo "❌ AVD '$AVD_NAME' not found."
    echo "Please run ./setup-emulators.sh first"
    exit 1
fi

# Check if APK exists
if [ ! -f "$APK_PATH" ]; then
    echo "❌ APK not found at: $APK_PATH"
    echo "Please build the APK first (./gradlew assembleRelease)"
    exit 1
fi

# Check if example PDF exists
if [ ! -f "$EXAMPLE_PDF" ]; then
    echo "❌ Example PDF not found at: $EXAMPLE_PDF"
    exit 1
fi

echo "✓ AVD: $AVD_NAME"
echo "✓ APK: $APK_PATH ($(du -h "$APK_PATH" | cut -f1))"
echo "✓ PDF: $EXAMPLE_PDF ($(du -h "$EXAMPLE_PDF" | cut -f1))"
echo ""

# Start emulator in background
echo "Starting emulator..."
echo "This may take 30-60 seconds for first boot."
echo ""
nohup emulator -avd "$AVD_NAME" -no-snapshot-save > emulator-phone.log 2>&1 &
EMULATOR_PID=$!
echo "Emulator PID: $EMULATOR_PID"
echo "Log file: emulator-phone.log"
echo ""

# Wait for device to boot
echo "Waiting for device to boot..."
adb wait-for-device
echo "✓ Device detected"
echo ""

# Wait for boot to complete
echo "Waiting for boot to complete..."
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
    echo -n "."
    sleep 2
done
echo ""
echo "✓ Boot completed"
echo ""

# Give it a few more seconds to settle
sleep 5

# Install APK
echo "Installing APK..."
adb install -r "$APK_PATH"
echo "✓ APK installed"
echo ""

# Push example PDF to Downloads
echo "Pushing example PDF to device..."
adb push "$EXAMPLE_PDF" "/sdcard/Download/example document.pdf"
echo "✓ PDF available in Downloads folder"
echo ""

echo "========================================="
echo "Emulator Ready for Screenshots!"
echo "========================================="
echo ""
echo "Device: Phone (Pixel 6, 6.4\", 1080x2400)"
echo "Package: com.svobodajakub.pdfg4compressor"
echo ""
echo "TAKING SCREENSHOTS:"
echo ""
echo "1. Launch the app from app drawer"
echo "2. Tap 'Choose PDF File' button"
echo "3. Navigate to Downloads folder"
echo "4. Select 'example document.pdf'"
echo "5. Take screenshot: Ctrl+S (or use toolbar button)"
echo "6. Optionally adjust settings and compress"
echo "7. Take additional screenshots showing the process"
echo ""
echo "Screenshots saved to: ~/Desktop/ (on host machine)"
echo ""
echo "CHANGING LANGUAGE:"
echo ""
echo "  Automated:  ./change-locale.sh de-DE"
echo "  Manual:     Settings → System → Languages & input"
echo ""
echo "COMMANDS:"
echo ""
echo "  Take screenshot:  Ctrl+S"
echo "  Change locale:    ./change-locale.sh de-DE"
echo "  Stop emulator:    adb emu kill"
echo "  Reinstall app:    adb install -r $APK_PATH"
echo ""
PHONE_EOF

cat > "run-emulator-tablet-7.sh" << 'TABLET7_EOF'
#!/bin/bash
set -e

echo "========================================="
echo "Screenshot Emulator - 7\" Tablet (Nexus 7)"
echo "========================================="
echo ""

# Setup environment
if [ -z "$ANDROID_HOME" ]; then
    export ANDROID_HOME="$HOME/Android"
fi
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

# Configuration
AVD_NAME="screenshot_tablet_7"
APK_PATH="app/build/outputs/apk/release/app-release.apk"
EXAMPLE_PDF="../example document.pdf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Check if AVD exists
if ! avdmanager list avd | grep -q "Name: $AVD_NAME"; then
    echo "❌ AVD '$AVD_NAME' not found."
    echo "Please run ./setup-emulators.sh first"
    exit 1
fi

# Check if APK exists
if [ ! -f "$APK_PATH" ]; then
    echo "❌ APK not found at: $APK_PATH"
    echo "Please build the APK first (./gradlew assembleRelease)"
    exit 1
fi

# Check if example PDF exists
if [ ! -f "$EXAMPLE_PDF" ]; then
    echo "❌ Example PDF not found at: $EXAMPLE_PDF"
    exit 1
fi

echo "✓ AVD: $AVD_NAME"
echo "✓ APK: $APK_PATH ($(du -h "$APK_PATH" | cut -f1))"
echo "✓ PDF: $EXAMPLE_PDF ($(du -h "$EXAMPLE_PDF" | cut -f1))"
echo ""

# Start emulator in background
echo "Starting emulator..."
echo "This may take 30-60 seconds for first boot."
echo ""
nohup emulator -avd "$AVD_NAME" -no-snapshot-save > emulator-tablet-7.log 2>&1 &
EMULATOR_PID=$!
echo "Emulator PID: $EMULATOR_PID"
echo "Log file: emulator-tablet-7.log"
echo ""

# Wait for device to boot
echo "Waiting for device to boot..."
adb wait-for-device
echo "✓ Device detected"
echo ""

# Wait for boot to complete
echo "Waiting for boot to complete..."
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
    echo -n "."
    sleep 2
done
echo ""
echo "✓ Boot completed"
echo ""

# Give it a few more seconds to settle
sleep 5

# Install APK
echo "Installing APK..."
adb install -r "$APK_PATH"
echo "✓ APK installed"
echo ""

# Push example PDF to Downloads
echo "Pushing example PDF to device..."
adb push "$EXAMPLE_PDF" "/sdcard/Download/example document.pdf"
echo "✓ PDF available in Downloads folder"
echo ""

echo "========================================="
echo "Emulator Ready for Screenshots!"
echo "========================================="
echo ""
echo "Device: 7-inch Tablet (Nexus 7, 7\", 800x1280)"
echo "Package: com.svobodajakub.pdfg4compressor"
echo ""
echo "TAKING SCREENSHOTS:"
echo ""
echo "1. Launch the app from app drawer"
echo "2. Tap 'Choose PDF File' button"
echo "3. Navigate to Downloads folder"
echo "4. Select 'example document.pdf'"
echo "5. Take screenshot: Ctrl+S (or use toolbar button)"
echo "6. Optionally adjust settings and compress"
echo "7. Take additional screenshots showing the process"
echo ""
echo "Screenshots saved to: ~/Desktop/ (on host machine)"
echo ""
echo "CHANGING LANGUAGE:"
echo ""
echo "  Automated:  ./change-locale.sh de-DE"
echo "  Manual:     Settings → System → Languages & input"
echo ""
echo "COMMANDS:"
echo ""
echo "  Take screenshot:  Ctrl+S"
echo "  Change locale:    ./change-locale.sh es-ES"
echo "  Stop emulator:    adb emu kill"
echo "  Reinstall app:    adb install -r $APK_PATH"
echo ""
TABLET7_EOF

cat > "run-emulator-tablet-10.sh" << 'TABLET10_EOF'
#!/bin/bash
set -e

echo "========================================="
echo "Screenshot Emulator - 10\" Tablet (Pixel Tablet)"
echo "========================================="
echo ""

# Setup environment
if [ -z "$ANDROID_HOME" ]; then
    export ANDROID_HOME="$HOME/Android"
fi
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

# Configuration
AVD_NAME="screenshot_tablet_10"
APK_PATH="app/build/outputs/apk/release/app-release.apk"
EXAMPLE_PDF="../example document.pdf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Check if AVD exists
if ! avdmanager list avd | grep -q "Name: $AVD_NAME"; then
    echo "❌ AVD '$AVD_NAME' not found."
    echo "Please run ./setup-emulators.sh first"
    exit 1
fi

# Check if APK exists
if [ ! -f "$APK_PATH" ]; then
    echo "❌ APK not found at: $APK_PATH"
    echo "Please build the APK first (./gradlew assembleRelease)"
    exit 1
fi

# Check if example PDF exists
if [ ! -f "$EXAMPLE_PDF" ]; then
    echo "❌ Example PDF not found at: $EXAMPLE_PDF"
    exit 1
fi

echo "✓ AVD: $AVD_NAME"
echo "✓ APK: $APK_PATH ($(du -h "$APK_PATH" | cut -f1))"
echo "✓ PDF: $EXAMPLE_PDF ($(du -h "$EXAMPLE_PDF" | cut -f1))"
echo ""

# Start emulator in background
echo "Starting emulator..."
echo "This may take 30-60 seconds for first boot."
echo ""
nohup emulator -avd "$AVD_NAME" -no-snapshot-save > emulator-tablet-10.log 2>&1 &
EMULATOR_PID=$!
echo "Emulator PID: $EMULATOR_PID"
echo "Log file: emulator-tablet-10.log"
echo ""

# Wait for device to boot
echo "Waiting for device to boot..."
adb wait-for-device
echo "✓ Device detected"
echo ""

# Wait for boot to complete
echo "Waiting for boot to complete..."
while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
    echo -n "."
    sleep 2
done
echo ""
echo "✓ Boot completed"
echo ""

# Give it a few more seconds to settle
sleep 5

# Install APK
echo "Installing APK..."
adb install -r "$APK_PATH"
echo "✓ APK installed"
echo ""

# Push example PDF to Downloads
echo "Pushing example PDF to device..."
adb push "$EXAMPLE_PDF" "/sdcard/Download/example document.pdf"
echo "✓ PDF available in Downloads folder"
echo ""

echo "========================================="
echo "Emulator Ready for Screenshots!"
echo "========================================="
echo ""
echo "Device: 10-inch Tablet (Pixel Tablet, 10.95\", 1600x2560)"
echo "Package: com.svobodajakub.pdfg4compressor"
echo ""
echo "TAKING SCREENSHOTS:"
echo ""
echo "1. Launch the app from app drawer"
echo "2. Tap 'Choose PDF File' button"
echo "3. Navigate to Downloads folder"
echo "4. Select 'example document.pdf'"
echo "5. Take screenshot: Ctrl+S (or use toolbar button)"
echo "6. Optionally adjust settings and compress"
echo "7. Take additional screenshots showing the process"
echo ""
echo "Screenshots saved to: ~/Desktop/ (on host machine)"
echo ""
echo "CHANGING LANGUAGE:"
echo ""
echo "  Automated:  ./change-locale.sh de-DE"
echo "  Manual:     Settings → System → Languages & input"
echo ""
echo "COMMANDS:"
echo ""
echo "  Take screenshot:  Ctrl+S"
echo "  Change locale:    ./change-locale.sh cs-CZ"
echo "  Stop emulator:    adb emu kill"
echo "  Reinstall app:    adb install -r $APK_PATH"
echo ""
TABLET10_EOF

cat > "change-locale.sh" << 'LOCALE_EOF'
#!/bin/bash

echo "========================================="
echo "Android Emulator Locale Changer"
echo "========================================="
echo ""

# Setup environment
if [ -z "$ANDROID_HOME" ]; then
    export ANDROID_HOME="$HOME/Android"
fi
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

# Check if device is connected
if ! adb devices | grep -q "emulator"; then
    echo "❌ No emulator detected."
    echo "Please start an emulator first:"
    echo "  ./run-emulator-phone.sh"
    echo "  ./run-emulator-tablet-7.sh"
    echo "  ./run-emulator-tablet-10.sh"
    exit 1
fi

# Display current locale
CURRENT_LOCALE=$(adb shell getprop persist.sys.locale)
echo "Current locale: $CURRENT_LOCALE"
echo ""

# Show available locales
echo "Quick locale codes (app has 67 languages):"
echo ""
echo "  en-US    English (United States)"
echo "  de-DE    German (Germany)"
echo "  es-ES    Spanish (Spain)"
echo "  fr-FR    French (France)"
echo "  it-IT    Italian (Italy)"
echo "  pt-BR    Portuguese (Brazil)"
echo "  cs-CZ    Czech (Czechia)"
echo "  sk-SK    Slovak (Slovakia)"
echo "  pl-PL    Polish (Poland)"
echo "  ru-RU    Russian (Russia)"
echo "  uk-UA    Ukrainian (Ukraine)"
echo "  zh-CN    Chinese Simplified (China)"
echo "  zh-TW    Chinese Traditional (Taiwan)"
echo "  ja-JP    Japanese (Japan)"
echo "  ko-KR    Korean (South Korea)"
echo "  ar-SA    Arabic (Saudi Arabia) - RTL"
echo "  he-IL    Hebrew (Israel) - RTL"
echo "  tr-TR    Turkish (Turkey)"
echo "  hi-IN    Hindi (India)"
echo "  ta-IN    Tamil (India)"
echo "  th-TH    Thai (Thailand)"
echo "  vi-VN    Vietnamese (Vietnam)"
echo "  id-ID    Indonesian (Indonesia)"
echo ""

# Get user input
if [ -z "$1" ]; then
    echo -n "Enter locale code (e.g., de-DE, es-ES, cs-CZ): "
    read LOCALE
else
    LOCALE="$1"
fi

if [ -z "$LOCALE" ]; then
    echo "❌ No locale specified."
    exit 1
fi

# Extract language and country
LANG_CODE=$(echo "$LOCALE" | cut -d'-' -f1)
COUNTRY_CODE=$(echo "$LOCALE" | cut -d'-' -f2)

if [ -z "$COUNTRY_CODE" ]; then
    COUNTRY_CODE=$(echo "$LANG_CODE" | tr '[:lower:]' '[:upper:]')
    LOCALE="${LANG_CODE}-${COUNTRY_CODE}"
fi

echo ""
echo "Setting locale to: $LOCALE"
echo ""

# Set locale using adb
adb shell "setprop persist.sys.locale $LOCALE; setprop ctl.restart zygote"

echo "✓ Locale changed to $LOCALE"
echo ""
echo "NOTE: The Android system UI will restart."
echo "Wait ~10 seconds, then reopen the app."
echo ""

# Optional: Kill app to force restart with new locale
sleep 2
adb shell "am force-stop com.svobodajakub.pdfg4compressor" 2>/dev/null || true
echo "✓ App restarted"
echo ""
echo "Open the app from the app drawer to see the new language."
echo ""
LOCALE_EOF

cat > "QUICK-START.txt" << 'QUICKSTART_EOF'
================================================================================
GOOGLE PLAY STORE SCREENSHOTS - QUICK START GUIDE
================================================================================

STEP 1: SETUP (ONE-TIME)
--------------------------------------------------------------------------------
cd android-build
./setup-emulators.sh

This creates 3 emulator devices required by Google Play Store.


STEP 2: TAKE SCREENSHOTS
--------------------------------------------------------------------------------

For PHONE screenshots:
    ./run-emulator-phone.sh

For 7-INCH TABLET screenshots:
    ./run-emulator-tablet-7.sh

For 10-INCH TABLET screenshots:
    ./run-emulator-tablet-10.sh

Each script:
    ✓ Starts emulator (wait 30-60 sec)
    ✓ Installs APK
    ✓ Loads example PDF
    ✓ Shows instructions


STEP 3: IN THE EMULATOR
--------------------------------------------------------------------------------

1. Open app from app drawer
2. Tap "Choose PDF File"
3. Select "example document.pdf" from Downloads
4. Press Ctrl+S to take screenshot
5. Adjust settings, tap "Compress to G4"
6. Take 1-7 more screenshots showing the process

Screenshots saved to: ~/Desktop/


STEP 4: CHANGE LANGUAGE (for localized screenshots)
--------------------------------------------------------------------------------

AUTOMATED (recommended):
    ./change-locale.sh de-DE        # German
    ./change-locale.sh es-ES        # Spanish
    ./change-locale.sh cs-CZ        # Czech
    ./change-locale.sh zh-CN        # Chinese Simplified

    (System UI restarts ~10 seconds, then reopen app)

MANUAL (alternative):
    Settings → System → Languages & input → Languages → Add (+)
    Select language → Drag to top → Reopen app

Supported: 67 languages (English, German, Spanish, Czech, Chinese, etc.)


GOOGLE PLAY REQUIREMENTS
--------------------------------------------------------------------------------

Minimum:  2 screenshots per device type (phone, 7", 10")
Maximum:  8 screenshots per device type
Format:   PNG or JPEG (24-bit)

Total minimum: 6 screenshots (2 × 3 devices)
Recommended:   12-15 screenshots (4-5 × 3 devices)


USEFUL COMMANDS
--------------------------------------------------------------------------------

Take screenshot:          Ctrl+S
Change locale:            ./change-locale.sh de-DE
Stop emulator:            adb emu kill
Reinstall APK:            adb install -r app/build/outputs/apk/release/app-release.apk
Push new PDF:             adb push file.pdf /sdcard/Download/
View logs:                adb logcat | grep -i pdf


FILES
--------------------------------------------------------------------------------

Setup script:             setup-emulators.sh
Phone emulator:           run-emulator-phone.sh
7" tablet emulator:       run-emulator-tablet-7.sh
10" tablet emulator:      run-emulator-tablet-10.sh
Locale changer:           change-locale.sh
Full documentation:       SCREENSHOTS-README.md
APK location:             app/build/outputs/apk/release/app-release.apk
Example PDF:              ../example document.pdf


TROUBLESHOOTING
--------------------------------------------------------------------------------

Problem: "AVD not found"
Fix:     Run ./setup-emulators.sh first

Problem: "APK not found"
Fix:     cd .. && ./gradlew assembleRelease

Problem: Emulator won't start
Fix:     Ensure ANDROID_HOME is set and system images are installed
         See SCREENSHOTS-README.md for detailed setup

Problem: Screenshots in wrong language
Fix:     Use ./change-locale.sh de-DE (or desired locale)

================================================================================
QUICKSTART_EOF

cat > "SCREENSHOTS-README.md" << 'SCREENSHOTS_EOF'
# Android Emulator Setup for Google Play Screenshots

This directory contains scripts to set up Android emulators and take screenshots for Google Play Store submission.

## Quick Start

### 1. First-Time Setup (One-Time)

Install Android SDK if not already installed:

```bash
# Create Android SDK directory
mkdir -p ~/Android/cmdline-tools
cd ~/Android/cmdline-tools

# Download command-line tools
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mv cmdline-tools latest
rm commandlinetools-linux-11076708_latest.zip

# Set up environment (add to ~/.bashrc for persistence)
export ANDROID_HOME=~/Android
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH

# Accept licenses
yes | sdkmanager --licenses

# Install required components (~500MB download, 5-10 minutes)
sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' 'emulator' 'system-images;android-34;google_apis;x86_64'
```

### 2. Create Emulator Devices

```bash
cd android-build
./setup-emulators.sh
```

This creates three Android Virtual Devices (AVDs):
- **screenshot_phone** - Pixel 6 (6.4", 1080x2400)
- **screenshot_tablet_7** - Nexus 7 (7", 800x1280)
- **screenshot_tablet_10** - Pixel Tablet (10.95", 1600x2560)

### 3. Run Emulators and Take Screenshots

**Phone screenshots:**
```bash
./run-emulator-phone.sh
```

**7-inch tablet screenshots:**
```bash
./run-emulator-tablet-7.sh
```

**10-inch tablet screenshots:**
```bash
./run-emulator-tablet-10.sh
```

Each script will:
1. Start the emulator (30-60 seconds for first boot)
2. Wait for boot completion
3. Install the APK
4. Push "example document.pdf" to Downloads folder
5. Display instructions

## Taking Screenshots

### In the Emulator

1. **Launch the app** from the app drawer (PDF G4 Compressor icon)
2. **Choose file**: Tap "Choose PDF File" button
3. **Select PDF**: Navigate to Downloads → "example document.pdf"
4. **Take screenshot**: Press `Ctrl+S` or click camera icon in emulator toolbar
5. **Compress** (optional): Adjust settings and tap "Compress to G4"
6. **Take more screenshots** showing the process

Screenshots are saved to `~/Desktop/` on your host machine.

### Recommended Screenshots per Device

Google Play requires **2-8 screenshots** per device type. Recommended:

1. **Main screen** - Clean UI with "Choose PDF File" button
2. **File selected** - Shows filename and options visible
3. **Settings shown** - DPI slider, conversion mode options
4. **Processing** - "Processing..." spinner visible
5. **Save dialog** - File save prompt after compression

## Changing Language/Locale

### Method 1: Automated Script (Recommended)

Use the `change-locale.sh` script to quickly switch languages:

```bash
./change-locale.sh de-DE    # German
./change-locale.sh es-ES    # Spanish
./change-locale.sh cs-CZ    # Czech
./change-locale.sh fr-FR    # French
./change-locale.sh zh-CN    # Chinese Simplified
./change-locale.sh ja-JP    # Japanese
./change-locale.sh ar-SA    # Arabic (RTL)
./change-locale.sh he-IL    # Hebrew (RTL)
```

The script will:
- Change the system locale
- Restart the Android system UI (~10 seconds)
- Force-stop the app
- You can then reopen the app in the new language

### Method 2: Manual (Alternative)

To change locale manually in the emulator:

1. Swipe down from top → tap **Settings** (gear icon)
2. Navigate to **System** → **Languages & input** → **Languages**
3. Tap **+** to add a language
4. Search and select desired language (e.g., German, Spanish, Czech)
5. **Drag the new language to the top** of the list
6. Return to home screen and **reopen the app**
7. The app will now display in the selected language

### Supported Languages (67 total)

The app auto-detects the system language and supports:
- English, German, Spanish, Portuguese, French, Italian
- Czech, Slovak, Polish, Russian, Ukrainian, Bulgarian
- Chinese (Simplified & Traditional), Japanese, Korean
- Arabic, Hebrew, Turkish, Persian
- Hindi, Tamil, Bengali, Telugu, Marathi, Gujarati, Punjabi, Urdu
- Thai, Vietnamese, Indonesian, Tagalog
- And 40+ more languages

## Useful Commands

```bash
# Take screenshot
Ctrl+S  # (or click camera icon in emulator toolbar)

# Change locale (automated)
./change-locale.sh de-DE    # Change to German
./change-locale.sh es-ES    # Change to Spanish

# View app logs
adb logcat | grep -i 'pdf\|g4\|compress'

# Reinstall app after rebuild
adb install -r app/build/outputs/apk/release/app-release.apk

# Push different PDF for testing
adb push /path/to/file.pdf /sdcard/Download/

# Uninstall app
adb uninstall com.svobodajakub.pdfg4compressor

# Stop emulator
adb emu kill

# List all running emulators
adb devices
```

## Google Play Store Requirements

### Screenshot Requirements

- **Minimum**: 2 screenshots per device type
- **Maximum**: 8 screenshots per device type
- **Device types required**: Phone, 7-inch tablet, 10-inch tablet
- **Format**: JPEG or PNG (24-bit)
- **Dimensions**:
  - Phone: 1080x2400 (or device native)
  - 7" tablet: 800x1280 (or device native)
  - 10" tablet: 1600x2560 (or device native)

### Localized Screenshots (Optional)

You can provide different screenshots for each language. Google Play supports localized listings.

To create localized screenshots:
1. Change emulator language using `./change-locale.sh de-DE`
2. Take new set of screenshots
3. Upload to corresponding language section in Play Console

## Troubleshooting

### Emulator won't start
- Check that `ANDROID_HOME` is set: `echo $ANDROID_HOME`
- Verify system image is installed: `sdkmanager --list_installed | grep system-images`
- Check available RAM: Emulator needs ~2GB RAM
- Enable virtualization in BIOS (Intel VT-x or AMD-V)

### APK not found
- Build the APK first: `./gradlew assembleRelease`
- Check path: `app/build/outputs/apk/release/app-release.apk`

### "example document.pdf" not found
- File should be at project root: `../example document.pdf`
- You can use any PDF - just update the path in the run script

### Emulator is slow
- Enable hardware acceleration: Check that GPU is enabled in AVD settings
- Increase RAM allocation: Edit AVD config to use more RAM
- Use KVM acceleration on Linux: Install `qemu-kvm` package

### Can't find screenshots
- Screenshots save to `~/Desktop/` by default
- Also check: `~/Pictures/` and the directory you launched emulator from
- File naming: `Screenshot_[timestamp].png`
- Check emulator settings: Tools → Extended controls → Settings → Screenshot save location

## Notes

- First boot of each emulator takes 30-60 seconds
- Subsequent boots are faster with snapshots (disabled in scripts for clean screenshots)
- Each emulator uses ~2GB RAM when running
- Screenshots are highest quality in PNG format
- Google Play Console will automatically resize screenshots if needed
SCREENSHOTS_EOF

chmod +x setup-emulators.sh run-emulator-phone.sh run-emulator-tablet-7.sh run-emulator-tablet-10.sh change-locale.sh

echo "✓ Created emulator setup and screenshot scripts"
echo ""

# Create BUILD-FORMATS.md documentation
cat > "BUILD-FORMATS.md" << 'BUILD_FORMATS_EOF'
# Android Build Formats: APK vs AAB

## Quick Reference

| Format | Use For | Build Command |
|--------|---------|---------------|
| **AAB** (`.aab`) | **Google Play publishing** | `./gradlew bundleRelease` |
| **APK** (`.apk`) | Local testing, emulators, sideloading | `./gradlew assembleRelease` |

## AAB (Android App Bundle)

**File**: `app/build/outputs/bundle/release/app-release.aab`

**What it is**: Google's publishing format that contains all compiled code and resources. Google Play generates optimized APKs from it for different device configurations.

**When to use**:
- ✅ Uploading to Google Play Console (required)
- ✅ Submitting for closed/open testing
- ✅ Publishing production releases

**Benefits**:
- Smaller downloads for users (Google Play serves optimized APKs)
- Supports dynamic feature modules
- Required by Google Play since August 2021

**Cannot**:
- ❌ Install directly on devices
- ❌ Use with `adb install`
- ❌ Share for sideloading

## APK (Android Package)

**File**: `app/build/outputs/apk/release/app-release.apk`

**What it is**: The traditional Android app format that can be installed directly on devices.

**When to use**:
- ✅ Testing on emulators (`adb install app-release.apk`)
- ✅ Installing on physical devices via USB
- ✅ Sideloading (sharing APK files directly)
- ✅ Taking screenshots in emulators

**Cannot**:
- ❌ Upload to Google Play (AAB required)

## Build Both

For a complete release workflow:

\`\`\`bash
cd android-build

# Build AAB for Google Play
./gradlew bundleRelease

# Build APK for local testing
./gradlew assembleRelease
\`\`\`

Both files are signed with the same keystore and have the same version code/name.

## File Sizes

Both formats are approximately **1.6 MB** for this app:
- AAB: ~1.6 MB (uploaded to Google Play)
- APK: ~1.6 MB (installed on devices)

Sizes are similar because this app:
- Has no native libraries (no ABI splits)
- Has no language-specific resources (minimal resource splits)
- Includes a single large HTML asset (~1.62 MB)

For apps with multiple ABIs or many localized resources, AAB produces much smaller downloads because Google Play only sends what each device needs.

## Version Management

Both AAB and APK use the same version from `src/build-apk.sh`:
- `VERSION_CODE`: Must increment for each Play Store upload
- `VERSION_NAME`: User-visible version string

## Signing

Both formats are signed with your release keystore:
- Keystore: `../android-private/release.keystore`
- Configuration: `../android-private/keystore.properties`

**Critical**: Keep `android-private/` backed up. Losing the keystore means you cannot update your app on Google Play.

## Google Play Upload Process

1. Build AAB: `./gradlew bundleRelease`
2. Upload `app/build/outputs/bundle/release/app-release.aab` to Play Console
3. Google Play validates and generates optimized APKs
4. Users download device-specific APKs (smaller than the full AAB)

## Testing Before Upload

While AAB is for publishing, you should test with APK first:

\`\`\`bash
# Build and install APK on emulator
./gradlew assembleRelease
adb install app/build/outputs/apk/release/app-release.apk

# Take screenshots for Play Store
./run-emulator-phone.sh
\`\`\`

Then build AAB for upload:

\`\`\`bash
./gradlew bundleRelease
# Upload app/build/outputs/bundle/release/app-release.aab to Play Console
\`\`\`

## References

- [Android App Bundle format](https://developer.android.com/guide/app-bundle)
- [Play App Signing](https://support.google.com/googleplay/android-developer/answer/9842756)
BUILD_FORMATS_EOF

cat > "QUICK-UPLOAD.txt" << 'UPLOAD_EOF'
================================================================================
GOOGLE PLAY UPLOAD - QUICK CHECKLIST
================================================================================

BEFORE UPLOADING
--------------------------------------------------------------------------------
☐ Increment version in src/build-apk.sh:
    VERSION_CODE=2       # Increment by 1
    VERSION_NAME="1.1"   # Update as desired

☐ Rebuild HTML if needed:
    cd src/webapp_build && python3 build.py

☐ Regenerate Android project:
    cd src && ./build-apk.sh

☐ Build AAB (required for Google Play):
    cd android-build && ./gradlew bundleRelease


FILE LOCATIONS
--------------------------------------------------------------------------------
Upload this file to Google Play Console:
    android-build/app/build/outputs/bundle/release/app-release.aab

For local testing (emulator/physical device):
    android-build/app/build/outputs/apk/release/app-release.apk


GOOGLE PLAY CONSOLE STEPS
--------------------------------------------------------------------------------
1. Go to: https://play.google.com/console
2. Select your app
3. Navigate to: Testing → Closed testing (or Production)
4. Create new release (or use existing track)
5. Upload app-release.aab
6. Fill in release notes
7. Review and roll out


FIRST-TIME UPLOAD REQUIREMENTS
--------------------------------------------------------------------------------
☐ App content questionnaire completed
☐ Store listing (title, description, screenshots)
☐ App category selected
☐ Content rating completed
☐ Privacy policy URL (if app handles user data)
☐ At least 2 screenshots per device type (phone, 7", 10")


VERSION REQUIREMENTS
--------------------------------------------------------------------------------
versionCode must INCREASE with each upload:
    Upload 1: versionCode=1
    Upload 2: versionCode=2
    Upload 3: versionCode=3
    (etc.)

versionName can be anything user-facing:
    "1.0", "1.1.0", "2.0-beta", etc.


TESTING TRACK OPTIONS
--------------------------------------------------------------------------------
Internal testing:    Up to 100 testers, instant rollout
Closed testing:      Limited testers, requires opt-in
Open testing:        Anyone can join, appears in Play Store
Production:          Public release to all users


COMMON ISSUES
--------------------------------------------------------------------------------
Problem: "Version code already used"
Fix:     Increment VERSION_CODE in src/build-apk.sh

Problem: "Upload failed: Signature error"
Fix:     Verify keystore is correct (android-private/release.keystore)
         Cannot change keystore after first upload

Problem: "Screenshots required"
Fix:     Upload screenshots using emulator scripts:
         ./run-emulator-phone.sh (minimum requirement)
         ./run-emulator-tablet-7.sh
         ./run-emulator-tablet-10.sh

Problem: "Privacy policy required"
Fix:     Add privacy policy URL in Play Console
         (Even offline apps may need one for Play Store compliance)


RELEASE NOTES TEMPLATE
--------------------------------------------------------------------------------
Version 1.0:
- Initial release
- Compress PDFs to CCITT Group 4 format
- Works 100% offline
- 67 languages supported

Version 1.1 (example):
- Bug fixes and improvements
- Updated translations


AFTER UPLOAD
--------------------------------------------------------------------------------
1. Wait for review (usually 1-3 days for first upload)
2. Check email for Google Play notifications
3. Once approved, share testing link with testers
4. Monitor crash reports in Play Console


USEFUL LINKS
--------------------------------------------------------------------------------
Play Console:        https://play.google.com/console
App Dashboard:       [Your app] → Dashboard
Release Management:  [Your app] → Testing or Production
Store Listing:       [Your app] → Store presence → Main store listing

================================================================================
UPLOAD_EOF

echo "✓ Created build format documentation and upload checklist"
echo ""

# Generate Android locale resources from JavaScript i18n
# This creates values-XX/strings.xml for all 84 languages, making them
# visible to Google Play Console
cat > "GENERATE-ANDROID-LOCALES.py" << 'LOCALE_SCRIPT_EOF'
#!/usr/bin/env python3
"""
Generate Android locale resource directories from JavaScript i18n files.

This script reads the JavaScript i18n translations and creates Android
resource directories (values-XX/strings.xml) for each language, making
them visible to Google Play Console.

WHEN TO RUN THIS SCRIPT:
========================

This script is AUTOMATICALLY run by src/build-apk.sh during Android project
generation. You do NOT need to run it manually under normal circumstances.

The script runs at this point in the build process:
  1. HTML built (src/webapp_build/build.py)
  2. Android project structure created (src/build-apk.sh)
  3. → THIS SCRIPT RUNS ← Creates locale directories
  4. AAB/APK built (./gradlew bundleRelease)

WHY THIS EXISTS:
================

Problem: Google Play Console only detects languages from Android resource
         directories (values-XX/strings.xml), NOT from JavaScript in the HTML.

Solution: This script creates minimal Android resource files for each language
          in your JavaScript i18n, making all 84 languages visible to Google Play.

Result: Google Play Console will correctly show all 84 supported languages
        instead of only the 87 from androidx.webkit dependency.

MANUAL USAGE (if needed):
==========================

If you modify language support (add/remove languages in i18n.js or
i18n-languages.js) and want to regenerate locale directories without
rebuilding the entire Android project:

    cd android-build
    python3 GENERATE-ANDROID-LOCALES.py
    ./gradlew bundleRelease

This will:
  - Read all languages from ../src/webapp_build/i18n*.js
  - Create values-XX/strings.xml for each language
  - Make them visible to Google Play Console

Usage:
    python3 GENERATE-ANDROID-LOCALES.py

Output:
    Creates app/src/main/res/values-XX/strings.xml for all languages
"""

import re
import os
from pathlib import Path

# Language code mapping: JavaScript → Android
# Android uses different codes for some languages
LOCALE_MAPPING = {
    # Chinese
    'zh-Hans': 'zh-rCN',  # Simplified Chinese
    'zh-Hant': 'zh-rTW',  # Traditional Chinese
    # Serbian
    'sr-Cyrl': 'sr',      # Serbian Cyrillic (default)
    'sr-Latn': 'b+sr+Latn',  # Serbian Latin (BCP 47)
    # Hebrew (Android legacy code)
    'he': 'iw',
    # Indonesian (Android legacy code)
    'id': 'in',
    # Yiddish (Android legacy code)
    'yi': 'ji',
    # Filipino = Tagalog in Android
    'fil': 'tl',
    # Note: mn-Mong (Traditional Mongolian) is skipped - Android resource system doesn't support it
}

def extract_languages_from_i18n(i18n_dir):
    """Extract all language codes and app names from i18n files."""
    i18n_files = [
        os.path.join(i18n_dir, 'i18n.js'),
        os.path.join(i18n_dir, 'i18n-languages.js'),
    ]

    languages = {}

    for filepath in i18n_files:
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern: language code followed by object with title field
        # Example: en: { title: "PDF Monochrome G4 Compressor", ...
        pattern = r"""
            ^\s+                          # Leading whitespace
            ['\"]?                        # Optional quote
            ([a-z]{2,3}(?:-[A-Za-z]+)?)  # Language code (captured)
            ['\"]?                        # Optional quote
            \s*:\s*\{                     # Colon and opening brace
            .*?                           # Anything
            title:\s*['"](.*?)['"]        # Title string (captured)
        """

        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL | re.VERBOSE)

        for match in matches:
            lang_code = match.group(1)
            title = match.group(2)
            languages[lang_code] = title

    return languages

def js_to_android_locale(js_code):
    """Convert JavaScript locale code to Android resource directory name."""
    return LOCALE_MAPPING.get(js_code, js_code)

def create_android_resources(languages, res_dir):
    """Create values-XX directories with strings.xml for each language."""
    created_count = 0

    for js_code, app_name in sorted(languages.items()):
        # Skip mn-Mong - Android resource system doesn't support it
        if js_code == 'mn-Mong':
            continue

        android_code = js_to_android_locale(js_code)

        # Create directory name
        if android_code == 'en':
            # English goes in default values/
            values_dir = os.path.join(res_dir, 'values')
        else:
            values_dir = os.path.join(res_dir, f'values-{android_code}')

        # Create directory
        os.makedirs(values_dir, exist_ok=True)

        # Create strings.xml
        strings_xml = os.path.join(values_dir, 'strings.xml')

        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{app_name}</string>
</resources>
'''

        with open(strings_xml, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        created_count += 1

    return created_count

def main():
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    i18n_dir = project_root / 'src' / 'webapp_build'
    res_dir = script_dir / 'app' / 'src' / 'main' / 'res'

    # Extract languages
    languages = extract_languages_from_i18n(i18n_dir)

    if not languages:
        print("ERROR: No languages found in i18n files!")
        return 1

    # Create Android resources
    created = create_android_resources(languages, res_dir)

    return 0

if __name__ == '__main__':
    exit(main())
LOCALE_SCRIPT_EOF

chmod +x GENERATE-ANDROID-LOCALES.py

# Run the locale generation script
echo "Generating Android locale resources from JavaScript i18n..."
python3 GENERATE-ANDROID-LOCALES.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Count generated locale directories
    LOCALE_COUNT=$(find app/src/main/res -name "values*" -type d | wc -l)
    echo "✓ Generated $LOCALE_COUNT locale resource directories"
else
    echo "⚠ Warning: Locale generation had issues, check GENERATE-ANDROID-LOCALES.py"
fi
echo ""

echo ""
echo "✓ Android project created!"
echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""
echo "App version: $VERSION_NAME (versionCode $VERSION_CODE)"
echo ""
echo "1. Create signing key (one-time):"
echo "   mkdir -p $KEYSTORE_DIR"
echo "   keytool -genkey -v -keystore $KEYSTORE_DIR/release.keystore \\"
echo "           -alias pdf-g4-key -keyalg RSA -keysize 2048 -validity 10000"
echo ""
echo "2. Create keystore.properties:"
echo "   cat > $KEYSTORE_DIR/keystore.properties << EOF"
echo "storeFile=android-private/release.keystore"
echo "storePassword=YOUR_PASSWORD"
echo "keyAlias=pdf-g4-key"
echo "keyPassword=YOUR_PASSWORD"
echo "EOF"
echo ""
echo "3. Build the release files:"
echo "   cd $BUILD_DIR"
echo "   ./gradlew bundleRelease    # For Google Play (AAB format)"
echo "   ./gradlew assembleRelease  # For direct install (APK format)"
echo ""
echo "4. Find release files at:"
echo "   AAB: $BUILD_DIR/app/build/outputs/bundle/release/app-release.aab"
echo "   APK: $BUILD_DIR/app/build/outputs/apk/release/app-release.apk"
echo ""
echo "APK/AAB will be fully offline with NO internet permission."
echo "Size: ~2.1 MB (includes ~2.1 MB HTML file)"
echo ""
echo "NOTE: Google Play requires AAB format for publishing."
echo "      APK is for local testing and sideloading only."
echo ""

# ============================================================================
# FIRST-TIME SETUP GUIDE (for rebuilding from scratch later)
# ============================================================================
#
# This section documents all the steps needed to set up the Android build
# environment on a fresh system. Save these instructions for future rebuilds.
#
# PREREQUISITES (install once):
# ------------------------------
#
# 1. Install Java JDK 21+ with development tools:
#
#    Fedora/RHEL:
#      sudo dnf install java-21-openjdk-devel
#
#    Ubuntu/Debian:
#      sudo apt install openjdk-21-jdk
#
#    Verify installation:
#      java -version    # Should show 21 or higher
#      jlink --version  # Should show 21 or higher (needed for Android builds)
#
#
# 2. Install Android SDK command-line tools:
#
#    mkdir -p ~/Android/cmdline-tools
#    cd ~/Android/cmdline-tools
#    curl -L https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -o cmdtools.zip
#    unzip cmdtools.zip
#    mv cmdline-tools latest
#    rm cmdtools.zip
#
#
# 3. Accept Android SDK licenses:
#
#    export ANDROID_HOME=~/Android
#    export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$PATH
#    yes | sdkmanager --licenses
#
#
# 4. Install required Android SDK components:
#
#    sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
#
#    This downloads ~500 MB and takes 5-10 minutes.
#
#
# 5. Create SDK location file (generated automatically by first build):
#
#    The file android-build/local.properties is created automatically with:
#      sdk.dir=/home/USERNAME/Android
#
#
# BUILDING THE APK:
# -----------------
#
# Once prerequisites are installed (one-time setup above), follow these steps
# every time you need to rebuild the APK:
#
# 1. Run this script to generate Android project:
#
#    cd src
#    ./build-apk.sh
#
#
# 2. Create signing keystore (FIRST BUILD ONLY):
#
#    mkdir -p android-private
#    keytool -genkey -v -keystore android-private/release.keystore \
#            -alias pdf-g4-key -keyalg RSA -keysize 2048 -validity 10000
#
#    You'll be prompted for:
#      - Keystore password (REMEMBER THIS!)
#      - Key password (press ENTER to use same as keystore password)
#      - Identity info (can press ENTER to skip all fields)
#
#    CRITICAL: Back up android-private/ directory! Loss = cannot update app!
#
#
# 3. Create keystore properties file (FIRST BUILD ONLY):
#
#    cat > android-private/keystore.properties << 'EOF'
#    storeFile=android-private/release.keystore
#    storePassword=YOUR_PASSWORD_HERE
#    keyAlias=pdf-g4-key
#    keyPassword=YOUR_PASSWORD_HERE
#    EOF
#
#    Replace YOUR_PASSWORD_HERE with the password you chose in step 2.
#
#
# 4. Build the release files:
#
#    cd android-build
#    ./gradlew bundleRelease      # AAB for Google Play (required)
#    ./gradlew assembleRelease    # APK for local testing
#
#    First build: 5-10 minutes (downloads Gradle and dependencies)
#    Subsequent builds: 30-60 seconds
#
#
# 5. Find the release files:
#
#    AAB: android-build/app/build/outputs/bundle/release/app-release.aab
#    APK: android-build/app/build/outputs/apk/release/app-release.apk
#
#    Upload the AAB file to Google Play Console.
#    Use the APK file for local testing and sideloading.
#
#
# TROUBLESHOOTING:
# ----------------
#
# Problem: "jlink executable does not exist"
# Solution: Install full JDK with -devel package (see step 1 above)
#
# Problem: "SDK location not found"
# Solution: Install Android SDK (see step 2-4 above)
#           Or create android-build/local.properties with:
#           sdk.dir=/home/USERNAME/Android
#
# Problem: "Keystore file not found"
# Solution: Check that android-private/keystore.properties has correct paths
#           Verify android-private/release.keystore exists
#
# Problem: "Minimum supported Gradle version"
# Solution: This script uses Gradle 8.7 which supports all current versions
#           If you see this, the gradle-wrapper.properties may be outdated
#
# Problem: Build fails with "package attribute deprecated"
# Solution: This is just a warning, can be ignored. Build still succeeds.
#
#
# DIRECTORY STRUCTURE:
# --------------------
#
# project-root/
# ├── src/
# │   ├── build-apk.sh              # This script
# │   ├── icon.svg                  # Source icon
# │   └── icon-512.png              # For Play Store
# ├── android-build/                # Generated by this script (gitignored)
# │   ├── app/
# │   │   ├── src/main/
# │   │   │   ├── AndroidManifest.xml
# │   │   │   ├── java/.../MainActivity.java
# │   │   │   ├── assets/index.html (your HTML)
# │   │   │   └── res/mipmap-*/ic_launcher.png
# │   │   └── build.gradle
# │   ├── local.properties          # SDK location (auto-generated)
# │   └── gradlew                   # Gradle wrapper
# └── android-private/              # BACKUP THIS! Don't commit to git!
#     ├── release.keystore          # Your signing key
#     └── keystore.properties       # Passwords
#
#
# UPDATING THE APP:
# -----------------
#
# To release an update:
#
# 1. Update the HTML file (run build.py if needed)
#
# 2. Increment version in src/build-apk.sh:
#      VERSION_CODE=2      # Increment by 1 (required by Play Store)
#      VERSION_NAME="1.1"  # Update as desired (shown to users)
#
# 3. Run this script again:
#      cd src && ./build-apk.sh
#
# 4. Rebuild:
#      cd android-build
#      ./gradlew bundleRelease    # For Google Play (AAB)
#      ./gradlew assembleRelease  # For testing (APK)
#
# 5. Upload AAB to Play Store:
#      android-build/app/build/outputs/bundle/release/app-release.aab
#
# Combo oneliner for rebuilds:
# ( cd src/webapp_build/ && python build.py ; ) && ( cd android-build/ && ./gradlew assembleRelease && ./gradlew bundleRelease ; )
#
# GOOGLE PLAY STORE:
# ------------------
#
# See ANDROID_BUILD.md for complete Play Store publishing guide.
#
# ============================================================================
