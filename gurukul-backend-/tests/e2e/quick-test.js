#!/usr/bin/env node

/**
 * Quick Test Runner - Fast feature verification
 * 
 * This script quickly tests all major features without full E2E setup.
 * Useful for quick smoke tests.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Gurukul Quick Test Runner\n');
console.log('This will test all major features quickly...\n');

// Test configuration
const config = {
  frontendUrl: 'http://localhost:5173',
  backendUrl: 'http://localhost:3000',
  karmaUrl: 'http://localhost:8001',
};

// Test results
const results = {
  passed: 0,
  failed: 0,
  skipped: 0,
  tests: []
};

// Helper to test URL
async function testUrl(url, name) {
  try {
    const response = await fetch(url);
    const status = response.status;
    const passed = status >= 200 && status < 400;
    
    results.tests.push({
      name,
      url,
      status,
      passed,
      message: passed ? 'OK' : `Status: ${status}`
    });
    
    if (passed) {
      results.passed++;
      console.log(`✅ ${name}: ${status}`);
    } else {
      results.failed++;
      console.log(`❌ ${name}: ${status}`);
    }
  } catch (error) {
    results.failed++;
    results.tests.push({
      name,
      url,
      status: 'ERROR',
      passed: false,
      message: error.message
    });
    console.log(`❌ ${name}: ${error.message}`);
  }
}

// Main test function
async function runQuickTests() {
  console.log('Testing Backend Endpoints...\n');
  
  // Backend health checks
  await testUrl(`${config.backendUrl}/health`, 'Backend Health');
  await testUrl(`${config.backendUrl}/api/v1/bucket/prana/status`, 'Bucket Status');
  
  console.log('\nTesting Frontend Pages...\n');
  
  // Frontend pages (these will fail if not logged in, but that's OK)
  const pages = [
    { path: '/', name: 'Home' },
    { path: '/signin', name: 'Sign In' },
    { path: '/signup', name: 'Sign Up' },
    { path: '/dashboard', name: 'Dashboard' },
    { path: '/subjects', name: 'Subjects' },
    { path: '/chatbot', name: 'Chatbot' },
    { path: '/summarizer', name: 'Summarizer' },
    { path: '/test', name: 'Test' },
    { path: '/lectures', name: 'Lectures' },
    { path: '/flashcards', name: 'Flashcards' },
  ];
  
  for (const page of pages) {
    try {
      const response = await fetch(`${config.frontendUrl}${page.path}`);
      const status = response.status;
      const passed = status >= 200 && status < 500; // 4xx is OK (auth required)
      
      results.tests.push({
        name: page.name,
        url: `${config.frontendUrl}${page.path}`,
        status,
        passed,
        message: passed ? 'OK' : `Status: ${status}`
      });
      
      if (passed) {
        results.passed++;
        console.log(`✅ ${page.name}: ${status}`);
      } else {
        results.failed++;
        console.log(`❌ ${page.name}: ${status}`);
      }
    } catch (error) {
      results.failed++;
      console.log(`❌ ${page.name}: ${error.message}`);
    }
  }
  
  console.log('\nTesting Karma Tracker...\n');
  await testUrl(`${config.karmaUrl}/health`, 'Karma Tracker Health');
  
  // Print summary
  console.log('\n' + '='.repeat(50));
  console.log('Test Summary');
  console.log('='.repeat(50));
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`⏭️  Skipped: ${results.skipped}`);
  console.log(`📊 Total: ${results.tests.length}`);
  console.log('='.repeat(50));
  
  // Save results
  const resultsPath = path.join(__dirname, 'quick-test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  console.log(`\n📄 Results saved to: ${resultsPath}`);
}

// Run tests
if (typeof fetch === 'undefined') {
  console.log('⚠️  Node.js 18+ required for fetch API');
  console.log('💡 Use: npm test (Playwright) instead');
  process.exit(1);
}

runQuickTests().catch(console.error);

