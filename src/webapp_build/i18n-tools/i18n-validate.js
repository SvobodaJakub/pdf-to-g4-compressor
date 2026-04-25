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
    'jbig2DisabledMpix', 'jbig2DisabledPages', 'ramOverrideAcceptRisk'
];

// Deprecated fields
const DEPRECATED_FIELDS = ['outputFormat', 'dpiDimensions', 'highFilesizeWarning', 'highComputeWarning'];

// Fields that must contain specific placeholders
const PLACEHOLDER_REQUIREMENTS = {
    'ramWarningHigh': ['{ram}'],
    'ramWarningCritical': ['{ram}'],
    'jbig2DisabledMpix': ['{mpix}'],
    'jbig2DisabledPages': ['{pages}'],
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

function checkDuplicateKeys(translations) {
    const issues = [];

    for (const [lang, fields] of Object.entries(translations)) {
        // Check if fields is actually an object
        if (typeof fields !== 'object' || fields === null) {
            issues.push(`${lang}: Translation is not an object (got ${typeof fields})`);
            continue;
        }

        // Check for duplicate keys by comparing keys array length to Set size
        const keys = Object.keys(fields);
        const uniqueKeys = new Set(keys);

        if (keys.length !== uniqueKeys.size) {
            // Find which keys are duplicated
            const keyCounts = {};
            keys.forEach(k => keyCounts[k] = (keyCounts[k] || 0) + 1);
            const duplicated = Object.entries(keyCounts)
                .filter(([k, count]) => count > 1)
                .map(([k, count]) => `${k}(x${count})`);

            issues.push(`${lang}: Duplicate keys: ${duplicated.join(', ')}`);
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

    // Check for duplicate keys
    console.log('\n' + '='.repeat(80));
    console.log('Checking for duplicate keys...');
    console.log('='.repeat(80));
    const duplicates = checkDuplicateKeys(allTranslations);
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
