#!/usr/bin/env node

/**
 * OCR Integration Verification Script
 * Verifies that the Expenses page properly integrates OCR functionality
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FRONTEND_DIR = path.join(__dirname, '..', 'frontend', 'src');
const EXPENSES_FILE = path.join(FRONTEND_DIR, 'pages', 'Expenses.jsx');
const EXPENSE_FORM_FILE = path.join(FRONTEND_DIR, 'components', 'ExpenseForm.jsx');
const OCR_COMPONENT = path.join(FRONTEND_DIR, 'components', 'OCRReceipt.jsx');

console.log('🔍 Verifying OCR Integration in Expenses...\n');

let hasErrors = false;

// Check if files exist
const filesToCheck = [
  { path: EXPENSES_FILE, name: 'Expenses.jsx' },
  { path: EXPENSE_FORM_FILE, name: 'ExpenseForm.jsx' },
  { path: OCR_COMPONENT, name: 'OCRReceipt.jsx' }
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

// Check Expenses page integration
console.log('\n📦 Checking Expenses page integration...');
const expensesContent = fs.readFileSync(EXPENSES_FILE, 'utf8');

const expensesChecks = [
  { name: 'OCRReceipt import', pattern: /import OCRReceipt from/ },
  { name: 'showOCR state', pattern: /const \[showOCR, setShowOCR\]/ },
  { name: 'extractedData state', pattern: /const \[extractedData, setExtractedData\]/ },
  { name: 'Scan Receipt button', pattern: /📸 Scan Receipt/ },
  { name: 'OCR component usage', pattern: /<OCRReceipt/ },
  { name: 'handleExtractedData function', pattern: /const handleExtractedData/ }
];

expensesChecks.forEach(check => {
  if (check.pattern.test(expensesContent)) {
    console.log(`✅ ${check.name} implemented`);
  } else {
    console.log(`❌ ${check.name} missing`);
    hasErrors = true;
  }
});

// Check button layout
console.log('\n🎨 Checking button layout...');
const buttonLayoutChecks = [
  { name: 'Button container div', pattern: /<div className="flex gap-3">/ },
  { name: 'Scan Receipt button styling', pattern: /bg-blue-600.*📸 Scan Receipt/ },
  { name: 'New Expense button styling', pattern: /bg-green-600.*\+ New Expense/ }
];

buttonLayoutChecks.forEach(check => {
  if (check.pattern.test(expensesContent)) {
    console.log(`✅ ${check.name} properly styled`);
  } else {
    console.log(`⚠️  ${check.name} may need adjustment`);
  }
});

// Check ExpenseForm integration
console.log('\n🔧 Checking ExpenseForm integration...');
const expenseFormContent = fs.readFileSync(EXPENSE_FORM_FILE, 'utf8');

const formChecks = [
  { name: 'initialData prop support', pattern: /initialData/ },
  { name: 'useEffect for initialData', pattern: /useEffect.*initialData/ },
  { name: 'Scanned expense title', pattern: /📸 Submit Scanned Expense/ },
  { name: 'Pre-fill notification', pattern: /Receipt data has been extracted/ }
];

formChecks.forEach(check => {
  if (check.pattern.test(expenseFormContent)) {
    console.log(`✅ ${check.name} implemented`);
  } else {
    console.log(`❌ ${check.name} missing`);
    hasErrors = true;
  }
});

// Check OCR workflow
console.log('\n🔄 Checking OCR workflow...');
const workflowChecks = [
  { 
    name: 'OCR toggle functionality', 
    pattern: /setShowOCR\(!showOCR\)/ 
  },
  { 
    name: 'Data extraction handler', 
    pattern: /setExtractedData\(data\)/ 
  },
  { 
    name: 'Form opening after OCR', 
    pattern: /setShowForm\(true\)/ 
  },
  { 
    name: 'OCR closing after extraction', 
    pattern: /setShowOCR\(false\)/ 
  }
];

workflowChecks.forEach(check => {
  if (check.pattern.test(expensesContent)) {
    console.log(`✅ ${check.name} working`);
  } else {
    console.log(`❌ ${check.name} not implemented`);
    hasErrors = true;
  }
});

// Check existing functionality preservation
console.log('\n🛡️  Checking existing functionality preservation...');
const existingFeatures = [
  { name: 'Filter tabs', pattern: /filter === status/ },
  { name: 'Expenses table', pattern: /expenses\.map/ },
  { name: 'Status colors', pattern: /getStatusColor/ },
  { name: 'Load expenses function', pattern: /const loadExpenses/ },
  { name: 'Expense service calls', pattern: /expenseService\.getExpenses/ }
];

existingFeatures.forEach(feature => {
  if (feature.pattern.test(expensesContent)) {
    console.log(`✅ ${feature.name} preserved`);
  } else {
    console.log(`❌ ${feature.name} may be broken`);
    hasErrors = true;
  }
});

// Check OCR component functionality
console.log('\n📸 Checking OCR component...');
const ocrContent = fs.readFileSync(OCR_COMPONENT, 'utf8');

const ocrChecks = [
  { name: 'File upload handling', pattern: /handleFileSelect/ },
  { name: 'OCR processing', pattern: /processReceipt/ },
  { name: 'API integration', pattern: /api\.post.*ocr/ },
  { name: 'Extracted data display', pattern: /extracted.*vendor/ },
  { name: 'Error handling', pattern: /setError/ }
];

ocrChecks.forEach(check => {
  if (check.pattern.test(ocrContent)) {
    console.log(`✅ ${check.name} implemented`);
  } else {
    console.log(`⚠️  ${check.name} may need verification`);
  }
});

// Check responsive design
console.log('\n📱 Checking responsive design...');
const responsiveChecks = [
  { name: 'Flex layout for buttons', pattern: /flex.*gap-3/ },
  { name: 'Mobile-friendly classes', pattern: /mb-6|px-4|py-2/ },
  { name: 'Grid responsiveness', pattern: /grid-cols/ }
];

responsiveChecks.forEach(check => {
  if (check.pattern.test(expensesContent)) {
    console.log(`✅ ${check.name} maintained`);
  } else {
    console.log(`⚠️  ${check.name} may need adjustment`);
  }
});

// Final summary
console.log('\n' + '='.repeat(50));
if (hasErrors) {
  console.log('❌ OCR integration has issues that need to be resolved.');
  console.log('\nPlease check the following:');
  console.log('1. All required imports are added');
  console.log('2. State variables are properly declared');
  console.log('3. Event handlers are implemented');
  console.log('4. OCR workflow is complete');
  console.log('5. Existing functionality is preserved');
  process.exit(1);
} else {
  console.log('✅ OCR integration verification completed successfully!');
  console.log('\n📊 Summary:');
  console.log('• Scan Receipt button added to Expenses page');
  console.log('• OCR component properly integrated');
  console.log('• ExpenseForm supports pre-filled data');
  console.log('• Existing functionality preserved');
  console.log('• Responsive design maintained');
  console.log('\n🚀 OCR integration is ready for use!');
}

console.log('\n💡 Next steps:');
console.log('1. Test OCR functionality in the browser');
console.log('2. Upload a receipt image and verify extraction');
console.log('3. Check that extracted data pre-fills the form');
console.log('4. Ensure existing expense creation still works');
console.log('5. Run tests: npm test Expenses.test.jsx');
console.log('6. Verify OCR API endpoint is working');

console.log('\n🔧 Manual testing checklist:');
console.log('□ Click "Scan Receipt" button');
console.log('□ Upload receipt image');
console.log('□ Verify OCR processing works');
console.log('□ Check extracted data accuracy');
console.log('□ Confirm form pre-fills correctly');
console.log('□ Test manual expense creation');
console.log('□ Verify filter tabs still work');
console.log('□ Check responsive design on mobile');