#!/bin/bash
# Setup script for Android APK build environment
# Uses Bubblewrap to convert the HTML app to Android APK

set -e

echo "======================================"
echo "Android APK Build Environment Setup"
echo "======================================"
echo ""

# Check Node.js
echo "Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    echo "Please install Node.js 14+ first:"
    echo "  https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✓ Node.js: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    echo "npm should come with Node.js"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo "✓ npm: $NPM_VERSION"

# Check Java
if ! command -v java &> /dev/null; then
    echo "❌ Java not found"
    echo "Please install JDK 11+ first:"
    echo "  sudo dnf install java-11-openjdk-devel  # Fedora/RHEL"
    echo "  sudo apt install openjdk-11-jdk         # Debian/Ubuntu"
    exit 1
fi
JAVA_VERSION=$(java -version 2>&1 | head -n 1)
echo "✓ Java: $JAVA_VERSION"

echo ""

# Create build directory
BUILD_DIR="../apk-build"
echo "Creating build directory: $BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Initialize npm project
echo ""
echo "Initializing npm project..."
if [ ! -f package.json ]; then
    npm init -y
fi

# Install Bubblewrap CLI
echo ""
echo "Installing Bubblewrap CLI (Google's PWA → APK tool)..."
npm install --save-dev @bubblewrap/cli

echo ""
echo "======================================"
echo "✓ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure your HTML is hosted at an HTTPS URL (required for TWA)"
echo "   Current: https://svobodajakub.github.io/pdf-to-g4-compressor.html"
echo ""
echo "2. Initialize Bubblewrap project:"
echo "   cd apk-build"
echo "   npx bubblewrap init --manifest https://svobodajakub.github.io/manifest.json"
echo ""
echo "3. Configure the generated twa-manifest.json with your app details"
echo ""
echo "4. Build the APK:"
echo "   npx bubblewrap build"
echo ""
echo "5. Find the signed APK at:"
echo "   apk-build/app-release-signed.apk"
echo ""
echo "Note: First build will download Android SDK (~500MB)"
echo ""
echo "See ANDROID_APK_BUILD.md for detailed documentation"
echo ""
