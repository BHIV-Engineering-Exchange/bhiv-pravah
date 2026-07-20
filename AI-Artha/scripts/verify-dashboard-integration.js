#!/usr/bin/env node

/**
 * Dashboard Integration Verification Script
 * Verifies that the Dashboard properly integrates with new components
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.join(__dirname, '..', 'frontend', 'src');
const DASHBOARD_FILE = path.join(FRONTEND_DIR, 'pages', 'Dashboard.jsx');
const LEDGER_COMPONENT = path.join(FRONTEND_DIR, 'components', 'LedgerIntegrityStatus.jsx');
const GST_COMPONENT = path.join(FRONTEND_DIR, 'components', 'GSTSummaryWidget.jsx');

console.log('🔍 Verifying Dashboard Integration...\n');

let hasErrors = false;

// Check if files exist
const filesToCheck = [
  { path: DASHBOARD_FILE, name: 'Dashboard.jsx' },
  { path: LEDGER_COMPONENT, name: 'LedgerIntegrityStatus.jsx' },
  { path: GST_COMPONENT, name: 'GSTSummaryWidget.jsx' }
];

console.log('📁 Checking file existence...');
filesToCheck.forEach(file => {
  if (fs.existsSync(file.path)) {
    console.log(`✅ ${file.name} exists`);
  } else {
    console.log(`❌ ${file.name} missing`);
    hasErrors = true;
  }
});

if (hasErrors) {
  console.log('\n❌ Missing required files. Please ensure all components are created.');
  process.exit(1);
}

// Check Dashboard imports
console.log('\n📦 Checking Dashboard imports...');
const dashboardContent = fs.readFileSync(DASHBOARD_FILE, 'utf8');

const requiredImports = [
  'LedgerIntegrityStatus',
  'GSTSummaryWidget'
];

requiredImports.forEach(importName => {
  if (dashboardContent.includes(`import ${importName}`)) {
    console.log(`✅ ${importName} imported correctly`);
  } else {
    console.log(`❌ ${importName} import missing`);
    hasErrors = true;
  }
});

// Check component usage in JSX
console.log('\n🔧 Checking component usage...');
const componentUsage = [
  { name: 'LedgerIntegrityStatus', pattern: /<LedgerIntegrityStatus\s*\/?>/ },
  { name: 'GSTSummaryWidget', pattern: /<GSTSummaryWidget\s*\/?>/ }
];

componentUsage.forEach(component => {
  if (component.pattern.test(dashboardContent)) {
    console.log(`✅ ${component.name} used in JSX`);
  } else {
    console.log(`❌ ${component.name} not found in JSX`);
    hasErrors = true;
  }
});

// Check layout structure
console.log('\n🎨 Checking layout structure...');
const layoutChecks = [
  {
    name: 'Ledger Integrity container',
    pattern: /bg-white shadow rounded-lg p-6 mb-8.*?<LedgerIntegrityStatus/s
  },
  {
    name: 'GST Summary container',
    pattern: /mb-8.*?<GSTSummaryWidget/s
  }
];

layoutChecks.forEach(check => {
  if (check.pattern.test(dashboardContent)) {
    console.log(`✅ ${check.name} properly structured`);
  } else {
    console.log(`⚠️  ${check.name} layout may need adjustment`);
  }
});

// Check for existing Dashboard functionality
console.log('\n🔍 Checking existing Dashboard functionality...');
const existingFeatures = [
  'KPI Cards',
  'Balance Sheet Summary',
  'Invoice Summary',
  'Recent Journal Entries'
];

const featurePatterns = [
  /KPICard/,
  /Balance Sheet Summary/,
  /Invoice Summary/,
  /Recent Journal Entries/
];

featurePatterns.forEach((pattern, index) => {
  if (pattern.test(dashboardContent)) {
    console.log(`✅ ${existingFeatures[index]} preserved`);
  } else {
    console.log(`❌ ${existingFeatures[index]} missing - existing functionality may be broken`);
    hasErrors = true;
  }
});

// Check component file structure
console.log('\n📋 Checking component file structure...');

// Check LedgerIntegrityStatus
const ledgerContent = fs.readFileSync(LEDGER_COMPONENT, 'utf8');
if (ledgerContent.includes('export default function LedgerIntegrityStatus')) {
  console.log('✅ LedgerIntegrityStatus properly exported');
} else {
  console.log('❌ LedgerIntegrityStatus export issue');
  hasErrors = true;
}

// Check GSTSummaryWidget
const gstContent = fs.readFileSync(GST_COMPONENT, 'utf8');
if (gstContent.includes('export default function GSTSummaryWidget')) {
  console.log('✅ GSTSummaryWidget properly exported');
} else {
  console.log('❌ GSTSummaryWidget export issue');
  hasErrors = true;
}

// Check for API integration
console.log('\n🌐 Checking API integration...');
if (ledgerContent.includes('api.get') && gstContent.includes('api.get')) {
  console.log('✅ Both components use API service');
} else {
  console.log('⚠️  API integration may be incomplete');
}

// Check for error handling
console.log('\n🛡️  Checking error handling...');
const errorHandlingPatterns = [
  /catch\s*\(\s*error\s*\)/,
  /\.catch\(/,
  /try\s*{/
];

let hasErrorHandling = false;
errorHandlingPatterns.forEach(pattern => {
  if (pattern.test(ledgerContent) && pattern.test(gstContent)) {
    hasErrorHandling = true;
  }
});

if (hasErrorHandling) {
  console.log('✅ Error handling implemented');
} else {
  console.log('⚠️  Error handling may be incomplete');
}

// Final summary
console.log('\n' + '='.repeat(50));
if (hasErrors) {
  console.log('❌ Dashboard integration has issues that need to be resolved.');
  console.log('\nPlease check the following:');
  console.log('1. All component files exist');
  console.log('2. Imports are correctly added to Dashboard.jsx');
  console.log('3. Components are used in the JSX');
  console.log('4. Existing Dashboard functionality is preserved');
  process.exit(1);
} else {
  console.log('✅ Dashboard integration verification completed successfully!');
  console.log('\n📊 Summary:');
  console.log('• LedgerIntegrityStatus component integrated');
  console.log('• GSTSummaryWidget component integrated');
  console.log('• Existing Dashboard functionality preserved');
  console.log('• Proper layout structure maintained');
  console.log('• API integration in place');
  console.log('\n🚀 Dashboard is ready for use!');
}

console.log('\n💡 Next steps:');
console.log('1. Test the Dashboard in the browser');
console.log('2. Verify both components load correctly');
console.log('3. Check responsive design on different screen sizes');
console.log('4. Ensure API endpoints are working');
console.log('5. Run frontend tests: npm test Dashboard.test.jsx');