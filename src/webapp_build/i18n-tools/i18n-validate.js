#!/usr/bin/env node
/**
 * i18n Translation Validator
 *
 * Validates translation files by parsing actual JavaScript objects.
 * This is the authoritative validator (uses proper JS parsing, not regex).
 *
 * Usage:
 *   node i18n-tools/i18n-validate.js          # from webapp_build directory
 *   cd i18n-tools && node i18n-validate.js    # from i18n-tools directory
 */

const fs = require('fs');
const path = require('path');

// Required fields
const REQUIRED_FIELDS = [
    'title', 'subtitle', 'privacyNotice', 'chooseFile', 'conversionMode',
    'noDither', 'dither', 'ditherSelected', 'pageRangePlaceholder', 'pageRangeHint',
    'pageSize', 'pageSizeA4Portrait', 'pageSizeA4Landscape',
    'pageSizeLetterPortrait', 'pageSizeLetterLandscape', 'pageSizeLegalPortrait',
    'outputDpi', 'dpiStandard', 'dpiCustom', 'dpiHint',
    'compressButton', 'processing', 'credits', 'license', 'about',
    'lowQualityWarning',
    'resultSaveButton', 'resultRecommendIgnore', 'resultDidntCompressWell',
    'resultBecameBigger', 'resultAppPurpose', 'resultDitheringNote', 'resultDitheringAdvice',
    'advancedTricks', 'useJBIG2Label', 'jbig2Warning',
    'preserveRotationLabel', 'metadataSection', 'includeTimestampLabel',
    'ramWarningHigh', 'ramWarningCritical',
    'jbig2DisabledMpix', 'jbig2DisabledPages', 'ramOverrideAcceptRisk',
    'fileInfoPageCount', 'fileInfoFileSize', 'inputHint'
];

// Deprecated fields
const DEPRECATED_FIELDS = ['outputFormat', 'dpiDimensions', 'highFilesizeWarning', 'highComputeWarning'];

// Fields that must contain specific placeholders
const PLACEHOLDER_REQUIREMENTS = {
    'ramWarningHigh': ['{ram}'],
    'ramWarningCritical': ['{ram}'],
    'jbig2DisabledMpix': ['{mpix}'],
    'jbig2DisabledPages': ['{pages}'],
    'fileInfoPageCount': ['{pages}'],
    'fileInfoFileSize': ['{size}'],
};

function extractTranslationsFromFile(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');

    // Find the object declaration
    // Match: const TRANSLATIONS = { ... };
    // or: const ADDITIONAL_TRANSLATIONS = { ... };

    // Extract the object definition by finding matching braces
    const varMatch = content.match(/const\s+(TRANSLATIONS|ADDITIONAL_TRANSLATIONS)\s*=\s*\{/);
    if (!varMatch) {
        console.error(`Could not find TRANSLATIONS or ADDITIONAL_TRANSLATIONS in ${filepath}`);
        return {};
    }

    const startIndex = varMatch.index + varMatch[0].length - 1; // Position of opening brace

    // Find matching closing brace
    let braceCount = 0;
    let endIndex = -1;
    for (let i = startIndex; i < content.length; i++) {
        if (content[i] === '{') braceCount++;
        if (content[i] === '}') braceCount--;
        if (braceCount === 0) {
            endIndex = i;
            break;
        }
    }

    if (endIndex === -1) {
        console.error(`Could not find matching closing brace in ${filepath}`);
        return {};
    }

    // Extract the object literal
    const objectLiteral = content.substring(startIndex, endIndex + 1);

    // Now parse it as JSON (with some preprocessing)
    // We need to convert JavaScript object literal to valid JSON
    try {
        // Wrap in a statement that can be evaluated
        const code = `(${objectLiteral})`;
        const translations = eval(code);
        return translations;
    } catch (e) {
        console.error(`Error parsing object in ${filepath}:`, e.message);
        console.error(`First 500 chars: ${objectLiteral.substring(0, 500)}`);
        return {};
    }
}

function checkDuplicateKeysFromSource(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const varMatch = content.match(/const\s+(TRANSLATIONS|ADDITIONAL_TRANSLATIONS)\s*=\s*\{/);
    if (!varMatch) return [];

    const objStart = varMatch.index + varMatch[0].length;
    const issues = [];
    let depth = 1;
    let inString = false;
    let escaped = false;
    let inLineComment = false;
    let currentLang = null;
    const langKeys = {};
    let ident = '';
    let quotedName = '';
    let stringStart = -1;

    for (let i = objStart; i < content.length; i++) {
        const ch = content[i];

        if (inLineComment) {
            if (ch === '\n') inLineComment = false;
            continue;
        }

        if (escaped) {
            escaped = false;
            continue;
        }

        if (inString) {
            if (ch === '\\') { escaped = true; continue; }
            if (ch === inString) {
                quotedName = content.substring(stringStart + 1, i);
                inString = false;
            }
            continue;
        }

        if (ch === '/' && i + 1 < content.length && content[i + 1] === '/') {
            inLineComment = true;
            ident = '';
            continue;
        }

        if (ch === '"' || ch === "'") {
            inString = ch;
            stringStart = i;
            ident = '';
            quotedName = '';
            continue;
        }

        if (ch === '{') { depth++; ident = ''; quotedName = ''; continue; }
        if (ch === '}') {
            if (depth === 2) currentLang = null;
            depth--;
            if (depth === 0) break;
            ident = ''; quotedName = '';
            continue;
        }

        if (ch === ':') {
            const key = ident.trim() || quotedName;
            if (key) {
                if (depth === 1) {
                    currentLang = key;
                    if (!langKeys[currentLang]) langKeys[currentLang] = [];
                } else if (depth === 2 && currentLang) {
                    langKeys[currentLang].push(key);
                }
            }
            ident = ''; quotedName = '';
            continue;
        }

        if (/[a-zA-Z0-9_$]/.test(ch)) {
            ident += ch;
            quotedName = '';
        } else if (ch === ',') {
            ident = ''; quotedName = '';
        }
    }

    for (const [lang, keys] of Object.entries(langKeys)) {
        const counts = {};
        keys.forEach(k => counts[k] = (counts[k] || 0) + 1);
        const dupes = Object.entries(counts)
            .filter(([, c]) => c > 1)
            .map(([k, c]) => `${k}(x${c})`);
        if (dupes.length > 0) {
            issues.push(`${lang}: Duplicate keys: ${dupes.join(', ')}`);
        }
    }
    return issues;
}

function checkMissingFields(translations) {
    const issues = [];

    for (const [lang, fields] of Object.entries(translations)) {
        if (typeof fields !== 'object' || fields === null) {
            continue;
        }

        const missing = REQUIRED_FIELDS.filter(f => !(f in fields));
        if (missing.length > 0) {
            issues.push(`${lang}: Missing ${missing.length} fields: ${missing.join(', ')}`);
        }
    }

    return issues;
}

function checkDeprecatedFields(translations) {
    const issues = [];

    for (const [lang, fields] of Object.entries(translations)) {
        if (typeof fields !== 'object' || fields === null) {
            continue;
        }

        const deprecated = DEPRECATED_FIELDS.filter(f => f in fields);
        if (deprecated.length > 0) {
            issues.push(`${lang}: Has deprecated fields: ${deprecated.join(', ')}`);
        }
    }

    return issues;
}

function checkExtraFields(translations) {
    const issues = [];
    const allAllowedFields = [...REQUIRED_FIELDS, ...DEPRECATED_FIELDS];

    for (const [lang, fields] of Object.entries(translations)) {
        if (typeof fields !== 'object' || fields === null) {
            continue;
        }

        const extra = Object.keys(fields).filter(f => !allAllowedFields.includes(f));
        if (extra.length > 0) {
            issues.push(`${lang}: Has unexpected fields: ${extra.join(', ')}`);
        }
    }

    return issues;
}

function checkEmptyValues(translations) {
    const issues = [];

    for (const [lang, fields] of Object.entries(translations)) {
        if (typeof fields !== 'object' || fields === null) {
            continue;
        }

        for (const [field, value] of Object.entries(fields)) {
            if (typeof value === 'string' && value.trim() === '') {
                issues.push(`${lang}.${field}: Empty string value`);
            } else if (typeof value !== 'string') {
                issues.push(`${lang}.${field}: Value is not a string (got ${typeof value})`);
            }
        }
    }

    return issues;
}

function main() {
    console.log('='.repeat(80));
    console.log('i18n Translation Validator (JavaScript Parser)');
    console.log('='.repeat(80));

    // Determine if we're running from i18n-tools/ or webapp_build/
    const cwd = process.cwd();
    const parentDir = path.basename(cwd) === 'i18n-tools' ? '..' : '.';

    const allTranslations = {};

    for (const filename of ['i18n.js', 'i18n-languages.js']) {
        const filepath = path.join(parentDir, filename);
        if (!fs.existsSync(filepath)) {
            console.log(`Warning: ${filepath} not found, skipping`);
            continue;
        }

        console.log(`\nLoading ${filepath}...`);
        const translations = extractTranslationsFromFile(filepath);
        Object.assign(allTranslations, translations);
        console.log(`  Found ${Object.keys(translations).length} languages`);
    }

    console.log(`\nTotal languages: ${Object.keys(allTranslations).length}`);
    console.log(`Languages: ${Object.keys(allTranslations).sort().join(', ')}`);

    let totalIssues = 0;

    // Check for duplicate keys (scans raw source text, not the eval'd object)
    console.log('\n' + '='.repeat(80));
    console.log('Checking for duplicate keys...');
    console.log('='.repeat(80));
    const duplicates = [];
    for (const filename of ['i18n.js', 'i18n-languages.js']) {
        const filepath = path.join(parentDir, filename);
        if (fs.existsSync(filepath)) {
            duplicates.push(...checkDuplicateKeysFromSource(filepath));
        }
    }
    if (duplicates.length > 0) {
        duplicates.forEach(issue => console.log(`  ❌ ${issue}`));
        totalIssues += duplicates.length;
    } else {
        console.log('  ✅ No duplicate keys found');
    }

    // Check for missing fields
    console.log('\n' + '='.repeat(80));
    console.log('Checking for missing required fields...');
    console.log('='.repeat(80));
    const missing = checkMissingFields(allTranslations);
    if (missing.length > 0) {
        missing.forEach(issue => console.log(`  ❌ ${issue}`));
        totalIssues += missing.length;
    } else {
        console.log('  ✅ All languages have required fields');
    }

    // Check for deprecated fields
    console.log('\n' + '='.repeat(80));
    console.log('Checking for deprecated fields...');
    console.log('='.repeat(80));
    const deprecated = checkDeprecatedFields(allTranslations);
    if (deprecated.length > 0) {
        deprecated.forEach(issue => console.log(`  ❌ ${issue}`));
        totalIssues += deprecated.length;
    } else {
        console.log('  ✅ No deprecated fields found');
    }

    // Check for unexpected extra fields
    console.log('\n' + '='.repeat(80));
    console.log('Checking for unexpected extra fields...');
    console.log('='.repeat(80));
    const extra = checkExtraFields(allTranslations);
    if (extra.length > 0) {
        extra.forEach(issue => console.log(`  ⚠️  ${issue}`));
        // Don't count as critical issues
    } else {
        console.log('  ✅ No unexpected fields found');
    }

    // Check for required placeholders
    console.log('\n' + '='.repeat(80));
    console.log('Checking for required placeholders...');
    console.log('='.repeat(80));
    const placeholderIssues = [];
    for (const [lang, fields] of Object.entries(allTranslations)) {
        if (typeof fields !== 'object' || fields === null) continue;
        for (const [field, placeholders] of Object.entries(PLACEHOLDER_REQUIREMENTS)) {
            if (field in fields) {
                for (const ph of placeholders) {
                    if (!fields[field].includes(ph)) {
                        placeholderIssues.push(`${lang}.${field}: Missing required placeholder ${ph}`);
                    }
                }
            }
        }
    }
    if (placeholderIssues.length > 0) {
        placeholderIssues.forEach(issue => console.log(`  ❌ ${issue}`));
        totalIssues += placeholderIssues.length;
    } else {
        console.log('  ✅ All required placeholders present');
    }

    // Check for empty values
    console.log('\n' + '='.repeat(80));
    console.log('Checking for empty string values...');
    console.log('='.repeat(80));
    const empty = checkEmptyValues(allTranslations);
    if (empty.length > 0) {
        empty.forEach(issue => console.log(`  ❌ ${issue}`));
        totalIssues += empty.length;
    } else {
        console.log('  ✅ No empty values found');
    }

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('SUMMARY');
    console.log('='.repeat(80));
    console.log(`Total critical issues found: ${totalIssues}`);

    if (totalIssues > 0) {
        console.log('\n❌ Validation FAILED - issues need to be fixed');
        process.exit(1);
    } else {
        console.log('\n✅ All structural validations PASSED');
        process.exit(0);
    }
}

main();
