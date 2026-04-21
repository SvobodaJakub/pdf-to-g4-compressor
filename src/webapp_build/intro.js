/**
 * Visual Introduction/Tutorial Animation
 *
 * Runs on every load (no persistent state) to show how the app works
 * Reuses existing UI and localization strings
 *
 * Copyright 2026 PDF Monochrome CCITT G4 Compressor Contributors
 * Licensed under the Apache License, Version 2.0
 */

'use strict';

const IntroAnimation = {
    isRunning: false,
    isCancelled: false,
    animationSpeed: 3, // Multiplier for animation durations (3 = 3x faster)
    offlineSpeedMultiplier: 1, // Additional multiplier for offline prelude
    demoSpeedMultiplier: 1, // Additional multiplier for PDF demo

    /**
     * Start the intro animation
     * @param {number} offlineSpeed - Speed multiplier for offline prelude (default 1)
     * @param {number} demoSpeed - Speed multiplier for PDF demo (default 1)
     */
    async start(offlineSpeed = 1, demoSpeed = 1) {
        if (this.isRunning) return;
        this.isRunning = true;
        this.isCancelled = false;

        // Store speed multipliers
        this.offlineSpeedMultiplier = offlineSpeed;
        this.demoSpeedMultiplier = demoSpeed;

        // Remove the early loading class
        document.documentElement.classList.remove('intro-mode-loading');

        // Turn help button into a close/cancel button
        this.setupCloseButton();

        // Create demo overlay (separate layer on top of normal UI)
        this.createDemoOverlay();

        // Make overlay visible immediately
        const overlay = document.getElementById('introOverlay');
        overlay.classList.add('visible');

        // Step 0: Show offline/privacy message with cloud icon
        await this.step0_showOfflineMessage();
        if (this.isCancelled) return;

        // Step 1: Auto-depress "Choose PDF File" button and show PDF icon
        await this.step1_choosePDF();
        if (this.isCancelled) return;

        // Step 2: Move PDF icon to "Compress" button and depress it
        await this.step2_moveToCompress();
        if (this.isCancelled) return;

        // Step 3: Show compression result
        await this.step3_showResult();
        if (this.isCancelled) return;

        // Step 4: Move to save button
        await this.step4_moveToSave();
        if (this.isCancelled) return;

        // Step 5: Transition to normal UI
        await this.step5_exitIntro();

        this.isRunning = false;
    },

    /**
     * Cancel the running demo immediately
     */
    cancel() {
        if (!this.isRunning) return;
        this.isCancelled = true;

        // Immediately remove all demo elements
        document.documentElement.classList.remove('intro-mode-loading');
        var overlay = document.getElementById('introOverlay');
        if (overlay) overlay.remove();
        var pdfIcon = document.getElementById('introPDFIcon');
        if (pdfIcon) pdfIcon.remove();

        this.restoreHelpButton();
        this.isRunning = false;
    },

    /**
     * Turn the help (?) button into a close (x) button above the overlay
     */
    setupCloseButton() {
        var helpBtn = document.getElementById('helpBtn');
        if (!helpBtn) return;
        this._helpBtnText = helpBtn.textContent;
        this._helpBtnAriaLabel = helpBtn.getAttribute('aria-label');
        helpBtn.textContent = '\u00d7';
        helpBtn.style.zIndex = '200000';
        helpBtn.setAttribute('aria-label', 'Stop demo');
        this._closeHandler = function(e) {
            e.stopImmediatePropagation();
            IntroAnimation.cancel();
        };
        helpBtn.addEventListener('click', this._closeHandler);
    },

    /**
     * Restore the help button to its normal state
     */
    restoreHelpButton() {
        var helpBtn = document.getElementById('helpBtn');
        if (!helpBtn) return;
        helpBtn.textContent = this._helpBtnText || '?';
        helpBtn.style.zIndex = '';
        helpBtn.setAttribute('aria-label', this._helpBtnAriaLabel || 'Show demo');
        if (this._closeHandler) {
            helpBtn.removeEventListener('click', this._closeHandler);
            this._closeHandler = null;
        }
    },

    createDemoOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'introOverlay';
        overlay.className = 'intro-overlay';
        overlay.setAttribute('aria-hidden', 'true');

        // Get current language for localized button text
        const currentT = (typeof TRANSLATIONS !== 'undefined' && typeof currentLang !== 'undefined')
            ? (TRANSLATIONS[currentLang] || TRANSLATIONS.en)
            : { chooseFile: 'Choose PDF File', compressButton: 'Compress' };

        overlay.innerHTML = `
            <div class="intro-container" id="introContainer">
                <div class="intro-upload-area">
                    <div class="intro-choose-btn" id="introChooseBtn">${currentT.chooseFile}</div>
                </div>
                <div class="intro-compress-btn intro-disabled" id="introCompressBtn">${currentT.compressButton}</div>
            </div>
        `;

        document.body.appendChild(overlay);
    },

    async step0_showOfflineMessage() {
        const container = document.getElementById('introContainer');
        const overlay = document.getElementById('introOverlay');

        // Get localized privacy notice text
        const currentT = (typeof TRANSLATIONS !== 'undefined' && typeof currentLang !== 'undefined')
            ? (TRANSLATIONS[currentLang] || TRANSLATIONS.en)
            : { privacyNotice: '🔒 Works 100% offline. Your PDFs never leave your device.' };

        // Create offline message with cloud icon
        const offlineMsg = document.createElement('div');
        offlineMsg.id = 'introOfflineMsg';
        offlineMsg.className = 'intro-offline-message';
        offlineMsg.innerHTML = `
            <svg class="intro-cloud-icon" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
                <!-- Globe (behind cloud) - positioned to right and slightly up, like overcast weather icon -->
                <circle cx="62" cy="40" r="20" fill="none" stroke="#3498db" stroke-width="2.5" opacity="0.75"/>
                <ellipse cx="62" cy="40" rx="9" ry="20" fill="none" stroke="#3498db" stroke-width="2" opacity="0.75"/>
                <line x1="42" y1="40" x2="82" y2="40" stroke="#3498db" stroke-width="2" opacity="0.75"/>
                <line x1="62" y1="20" x2="62" y2="60" stroke="#3498db" stroke-width="2" opacity="0.75"/>

                <!-- Cloud - partly covering globe (on the left side) -->
                <path d="M 25,50 Q 25,42 32,42 Q 32,35 40,35 Q 40,28 50,28 Q 60,28 60,35 Q 68,35 68,42 Q 75,42 75,50 Q 75,58 68,58 L 32,58 Q 25,58 25,50 Z"
                      fill="rgba(255, 255, 255, 0.9)" stroke="#667eea" stroke-width="2.5"/>

                <!-- Wireless icon - 3 concentric quarter-circle arcs (like WiFi) -->
                <!-- Center point at bottom, arcs radiating upward -->
                <circle cx="50" cy="54" r="2" fill="#667eea"/>
                <path d="M 42,54 A 8,8 0 0,1 50,46" fill="none" stroke="#667eea" stroke-width="2.5" stroke-linecap="round"/>
                <path d="M 38,54 A 12,12 0 0,1 50,42" fill="none" stroke="#667eea" stroke-width="2.5" stroke-linecap="round"/>
                <path d="M 34,54 A 16,16 0 0,1 50,38" fill="none" stroke="#667eea" stroke-width="2.5" stroke-linecap="round"/>

                <!-- Red cross (will be drawn with animation) -->
                <g id="introCross">
                    <line id="introCrossLine1" x1="20" y1="20" x2="80" y2="65" stroke="#e74c3c" stroke-width="6" stroke-linecap="round"
                          stroke-dasharray="78" stroke-dashoffset="78"/>
                    <line id="introCrossLine2" x1="80" y1="20" x2="20" y2="65" stroke="#e74c3c" stroke-width="6" stroke-linecap="round"
                          stroke-dasharray="78" stroke-dashoffset="78"/>
                </g>
            </svg>
            <p class="intro-privacy-text">${currentT.privacyNotice}</p>
        `;

        // Add offline message to overlay
        overlay.appendChild(offlineMsg);

        // Show the message
        offlineMsg.classList.add('visible');

        await this.wait(600, true); // 600/3 = 200ms to see the message (offline step)

        // Draw the cross immediately after message appears
        const line1 = document.getElementById('introCrossLine1');
        const line2 = document.getElementById('introCrossLine2');

        // Draw first line (200ms actual with speed 3)
        const crossDuration = 0.2 / this.offlineSpeedMultiplier;
        line1.style.transition = `stroke-dashoffset ${crossDuration}s ease-out`;
        line1.style.strokeDashoffset = '0';

        await this.wait(600, true); // 600/3 = 200ms actual (offline step)

        // Draw second line (200ms actual with speed 3)
        line2.style.transition = `stroke-dashoffset ${crossDuration}s ease-out`;
        line2.style.strokeDashoffset = '0';

        await this.wait(600, true); // 600/3 = 200ms actual (offline step)

        // Fade out the offline message and fade in container simultaneously
        offlineMsg.classList.add('fading');
        container.style.opacity = '1';

        await this.wait(600, true); // 600/3 = 200ms actual - total offline prelude = 800ms (200+200+200+200) (offline step)

        // Remove offline message
        offlineMsg.remove();
    },

    async step1_choosePDF() {
        const chooseBtn = document.getElementById('introChooseBtn');
        const uploadArea = document.querySelector('.intro-upload-area');

        // Depress the button
        chooseBtn.classList.add('intro-depressed');

        await this.wait(200);

        // Create and show PDF icon (slightly too large)
        const pdfIcon = this.createPDFIcon('large');
        pdfIcon.id = 'introPDFIcon';

        // Position it on the button
        const btnRect = chooseBtn.getBoundingClientRect();
        pdfIcon.style.left = `${btnRect.left + btnRect.width / 2}px`;
        pdfIcon.style.top = `${btnRect.top + btnRect.height / 2}px`;

        // Append to overlay so it's on the same z-plane
        const overlay = document.getElementById('introOverlay');
        overlay.appendChild(pdfIcon);

        // Animate in
        await this.wait(50);
        pdfIcon.classList.add('visible');

        await this.wait(800);

        // Release button
        chooseBtn.classList.remove('intro-depressed');

        await this.wait(300);
    },

    async step2_moveToCompress() {
        const pdfIcon = document.getElementById('introPDFIcon');
        const compressBtn = document.getElementById('introCompressBtn');

        // Enable compress button for visual purposes
        compressBtn.classList.remove('intro-disabled');

        // Move icon to compress button
        const btnRect = compressBtn.getBoundingClientRect();
        pdfIcon.style.left = `${btnRect.left + btnRect.width / 2}px`;
        pdfIcon.style.top = `${btnRect.top + btnRect.height / 2}px`;

        await this.wait(800);

        // Depress compress button
        compressBtn.classList.add('intro-depressed');

        await this.wait(200);

        // Shrink icon from large to small
        pdfIcon.classList.remove('size-large');
        pdfIcon.classList.add('size-small');

        await this.wait(400);
    },

    async step3_showResult() {
        const compressBtn = document.getElementById('introCompressBtn');

        // Create and show compression result
        // Handle RTL languages properly (same fix as in showResultBox)
        const rtlLanguages = new Set(['ar', 'he', 'ur', 'yi']);
        const isRTL = (typeof currentLang !== 'undefined' && rtlLanguages.has(currentLang));

        let sizeText;
        if (isRTL) {
            sizeText = '<span dir="ltr">1 MB → 80 kB</span>';
        } else {
            sizeText = '1 MB → 80 kB';
        }

        const result = document.createElement('div');
        result.id = 'introResult';
        result.className = 'intro-result';
        result.innerHTML = `
            <div class="intro-result-content">
                <span class="intro-size-change">${sizeText}</span>
            </div>
        `;

        // Insert after compress button (but invisible initially)
        const container = compressBtn.parentElement;
        container.appendChild(result);

        await this.wait(50);
        result.classList.add('visible');

        await this.wait(400);

        // Create save button
        const saveBtn = document.createElement('div');
        saveBtn.id = 'introSaveBtn';
        saveBtn.className = 'intro-save-btn';
        // Use existing localization
        const currentT = (typeof TRANSLATIONS !== 'undefined' && typeof currentLang !== 'undefined')
            ? (TRANSLATIONS[currentLang] || TRANSLATIONS.en)
            : { resultSaveButton: 'Save PDF' };
        saveBtn.textContent = currentT.resultSaveButton || 'Save PDF';

        result.appendChild(saveBtn);

        await this.wait(50);
        saveBtn.classList.add('visible');

        await this.wait(600);

        // Release compress button
        compressBtn.classList.remove('intro-depressed');

        await this.wait(200);
    },

    async step4_moveToSave() {
        const pdfIcon = document.getElementById('introPDFIcon');
        const saveBtn = document.getElementById('introSaveBtn');

        // Move icon to save button
        const btnRect = saveBtn.getBoundingClientRect();
        pdfIcon.style.left = `${btnRect.left + btnRect.width / 2}px`;
        pdfIcon.style.top = `${btnRect.top + btnRect.height / 2}px`;

        await this.wait(600);

        // Depress save button and fade out icon simultaneously
        saveBtn.classList.add('intro-depressed');
        pdfIcon.classList.add('fading');

        await this.wait(800);
    },

    async step5_exitIntro() {
        // Show main UI and fade out the demo overlay simultaneously
        document.documentElement.classList.remove('intro-mode-loading');

        const overlay = document.getElementById('introOverlay');
        if (overlay) {
            overlay.classList.add('intro-fading-out');
        }

        await this.wait(800);

        // Remove overlay completely
        if (overlay) {
            overlay.remove();
        }

        // Clean up PDF icon if it exists
        const pdfIcon = document.getElementById('introPDFIcon');
        if (pdfIcon) pdfIcon.remove();

        // Restore help button from close mode
        this.restoreHelpButton();

        // Done!
        this.isRunning = false;
    },

    /**
     * Create a PDF icon SVG element
     */
    createPDFIcon(size) {
        const icon = document.createElement('div');
        icon.className = `intro-pdf-icon size-${size}`;

        icon.innerHTML = `
            <svg viewBox="0 0 64 80" xmlns="http://www.w3.org/2000/svg">
                <!-- PDF document shape -->
                <path d="M 4 0 L 40 0 L 60 20 L 60 80 L 4 80 Z" fill="#E74C3C" stroke="#C0392B" stroke-width="2"/>
                <!-- Folded corner -->
                <path d="M 40 0 L 40 20 L 60 20 Z" fill="#C0392B"/>
                <!-- White lines representing text -->
                <rect x="12" y="30" width="40" height="3" fill="white" opacity="0.8"/>
                <rect x="12" y="38" width="40" height="3" fill="white" opacity="0.8"/>
                <rect x="12" y="46" width="30" height="3" fill="white" opacity="0.8"/>
                <!-- PDF text -->
                <text x="32" y="68" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white" text-anchor="middle">PDF</text>
            </svg>
        `;

        return icon;
    },

    /**
     * Wait for a duration (affected by speed multiplier)
     * @param {boolean} isOfflineStep - If true, uses offline speed multiplier, otherwise demo speed
     */
    wait(ms, isOfflineStep = false) {
        if (this.isCancelled) return Promise.resolve();
        const speedMultiplier = isOfflineStep ? this.offlineSpeedMultiplier : this.demoSpeedMultiplier;
        return new Promise(resolve => setTimeout(resolve, ms / this.animationSpeed / speedMultiplier));
    }
};

// Auto-start intro when page loads (after i18n is initialized)
// We'll call this from the main app initialization
if (typeof window !== 'undefined') {
    window.IntroAnimation = IntroAnimation;
}
