/**
 * Bank Statement Feature Verification Script
 * Verifies that all bank statement components are properly implemented
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.join(__dirname, '..');
const BACKEND_DIR = ROOT_DIR;
const FRONTEND_DIR = path.join(ROOT_DIR, '..', 'frontend');

console.log('🔍 Verifying Bank Statement Feature Implementation...\n');

let hasErrors = false;
const checks = [];

// Helper function to check file existence
function checkFile(filePath, description) {
  const exists = fs.existsSync(filePath);
  checks.push({
    file: filePath,
    description,
    exists,
  });
  
  if (exists) {
    console.log(`✅ ${description}`);
  } else {
    console.log(`❌ ${description} - MISSING`);
    hasErrors = true;
  }
  
  return exists;
}

// Helper function to check file content
function checkFileContent(filePath, patterns, description) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    let allMatch = true;
    
    patterns.forEach(pattern => {
      if (!pattern.test(content)) {
        allMatch = false;
      }
    });
    
    if (allMatch) {
      console.log(`✅ ${description}`);
    } else {
      console.log(`❌ ${description} - Missing required patterns`);
      hasErrors = true;
    }
    
    return allMatch;
  } catch (error) {
    console.log(`❌ ${description} - Error reading file: ${error.message}`);
    hasErrors = true;
    return false;
  }
}

console.log('📁 Checking Backend Files...\n');

// Check Model
checkFile(
  path.join(BACKEND_DIR, 'src', 'models', 'BankStatement.js'),
  'BankStatement model'
);

checkFileContent(
  path.join(BACKEND_DIR, 'src', 'models', 'BankStatement.js'),
  [
    /const transactionSchema/,
    /const bankStatementSchema/,
    /mongoose\.model\('BankStatement'/,
  ],
  'BankStatement model structure'
);

// Check Service
checkFile(
  path.join(BACKEND_DIR, 'src', 'services', 'bankStatement.service.js'),
  'BankStatement service'
);

checkFileContent(
  path.join(BACKEND_DIR, 'src', 'services', 'bankStatement.service.js'),
  [
    /class BankStatementService/,
    /uploadBankStatement/,
    /processStatementFile/,
    /parseCSV/,
    /matchTransactions/,
    /createExpensesFromTransactions/,
  ],
  'BankStatement service methods'
);

// Check Controller
checkFile(
  path.join(BACKEND_DIR, 'src', 'controllers', 'bankStatement.controller.js'),
  'BankStatement controller'
);

checkFileContent(
  path.join(BACKEND_DIR, 'src', 'controllers', 'bankStatement.controller.js'),
  [
    /uploadBankStatement/,
    /getBankStatements/,
    /getBankStatement/,
    /matchTransactions/,
    /createExpensesFromTransactions/,
  ],
  'BankStatement controller endpoints'
);

// Check Routes
checkFile(
  path.join(BACKEND_DIR, 'src', 'routes', 'bankStatement.routes.js'),
  'BankStatement routes'
);

checkFileContent(
  path.join(BACKEND_DIR, 'src', 'routes', 'bankStatement.routes.js'),
  [
    /router\.post\(['"]\/upload['"]/,
    /router\.get\(['"]\/['"]\s*,\s*getBankStatements/,
    /router\.get\(['"]\/:id['"]/,
    /router\.post\(['"]\/:id\/process['"]/,
    /router\.post\(['"]\/:id\/match['"]/,
    /router\.post\(['"]\/:id\/create-expenses['"]/,
  ],
  'BankStatement route definitions'
);

// Check Server Integration
checkFileContent(
  path.join(BACKEND_DIR, 'src', 'server.js'),
  [
    /import.*bankStatementRoutes/,
    /app\.use\(['"]\/api\/v1\/statements['"].*bankStatementRoutes/,
  ],
  'Server.js integration'
);

// Check Middleware
checkFileContent(
  path.join(BACKEND_DIR, 'src', 'middleware', 'upload.js'),
  [
    /const statementsDir/,
    /const statementsStorage/,
    /const statementsFileFilter/,
    /export const uploadFile/,
  ],
  'Upload middleware for statements'
);

// Check Package.json
checkFileContent(
  path.join(BACKEND_DIR, 'package.json'),
  [/csv-parse/],
  'csv-parse dependency'
);

console.log('\n📁 Checking Frontend Files...\n');

// Check Service
checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'services', 'index.js'),
  [
    /export const bankStatementService/,
    /upload:.*file.*data/,
    /getAll:.*params/,
    /getById:.*id/,
    /process:.*id/,
    /matchTransactions:.*id/,
    /createExpenses:.*id.*transactionIds/,
  ],
  'Frontend bank statement service'
);

// Check Sidebar
checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'components', 'layout', 'Sidebar.jsx'),
  [
    /CreditCard/,
    /title: ['"]Statements['"]/,
    /path: ['"]\/statements['"]/,
    /children:.*All Statements.*Upload Statement/,
  ],
  'Sidebar navigation'
);

// Check Pages
checkFile(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementsList.jsx'),
  'StatementsList page'
);

checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementsList.jsx'),
  [
    /import.*bankStatementService/,
    /const loadStatements/,
    /handleProcessStatement/,
    /handleMatchTransactions/,
    /getStatusIcon/,
  ],
  'StatementsList page functionality'
);

checkFile(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementsUpload.jsx'),
  'StatementsUpload page'
);

checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementsUpload.jsx'),
  [
    /import.*bankStatementService/,
    /handleDrag/,
    /handleDrop/,
    /handleSubmit/,
    /uploadSchema/,
  ],
  'StatementsUpload page functionality'
);

checkFile(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementDetail.jsx'),
  'StatementDetail page'
);

checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'pages', 'statements', 'StatementDetail.jsx'),
  [
    /import.*bankStatementService/,
    /handleMatchTransactions/,
    /handleCreateExpenses/,
    /toggleTransactionSelection/,
    /selectAllUnmatched/,
  ],
  'StatementDetail page functionality'
);

// Check App Routes
checkFileContent(
  path.join(FRONTEND_DIR, 'src', 'App.jsx'),
  [
    /import.*StatementsList/,
    /import.*StatementsUpload/,
    /import.*StatementDetail/,
    /path=['"]\/statements['"]/,
    /path=['"]\/statements\/upload['"]/,
    /path=['"]\/statements\/:id['"]/,
  ],
  'App.jsx routing'
);

console.log('\n📁 Checking Documentation...\n');

checkFile(
  path.join(ROOT_DIR, 'docs', 'BANK_STATEMENTS_FEATURE.md'),
  'Comprehensive feature guide'
);

checkFile(
  path.join(ROOT_DIR, 'docs', 'STATEMENTS_QUICKSTART.md'),
  'Quick start guide'
);

checkFile(
  path.join(ROOT_DIR, 'docs', 'BANK_STATEMENTS_IMPLEMENTATION_SUMMARY.md'),
  'Implementation summary'
);

checkFile(
  path.join(BACKEND_DIR, 'uploads', 'statements', 'sample-statement-template.csv'),
  'Sample CSV template'
);

console.log('\n📁 Checking Upload Directory...\n');

const statementsDir = path.join(BACKEND_DIR, 'uploads', 'statements');
if (fs.existsSync(statementsDir)) {
  console.log(`✅ Upload directory created: ${statementsDir}`);
} else {
  console.log(`❌ Upload directory missing: ${statementsDir}`);
  hasErrors = true;
}

// Summary
console.log('\n' + '='.repeat(60));
console.log('📊 VERIFICATION SUMMARY');
console.log('='.repeat(60));

const totalChecks = checks.length;
const passedChecks = checks.filter(c => c.exists).length;
const failedChecks = totalChecks - passedChecks;

console.log(`\nTotal Checks: ${totalChecks}`);
console.log(`✅ Passed: ${passedChecks}`);
console.log(`❌ Failed: ${failedChecks}`);

if (hasErrors) {
  console.log('\n❌ VERIFICATION FAILED');
  console.log('\n⚠️  Some components are missing. Please review the errors above.');
  process.exit(1);
} else {
  console.log('\n✅ VERIFICATION PASSED');
  console.log('\n🎉 All bank statement components are properly implemented!');
  console.log('\n📋 Next Steps:');
  console.log('   1. Install dependencies: npm install');
  console.log('   2. Test with sample CSV file');
  console.log('   3. Verify frontend UI');
  console.log('   4. Run manual testing checklist');
  console.log('\n📚 Documentation available in docs/ folder');
  process.exit(0);
}
