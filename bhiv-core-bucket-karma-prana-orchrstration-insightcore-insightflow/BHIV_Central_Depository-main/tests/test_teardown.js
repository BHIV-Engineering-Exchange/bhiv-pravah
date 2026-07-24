/**
 * Jest Global Test Teardown
 * Cleans up test environment and generates final reports
 */

const fs = require('fs').promises;
const path = require('path');

module.exports = async () => {
  console.log('🧹 Test environment teardown...');

  try {
    // Check for test results
    const testResultsDir = path.join(__dirname, 'test_results');
    const files = await fs.readdir(testResultsDir).catch(() => []);

    if (files.length > 0) {
      console.log(`📊 Test results saved (${files.length} files):`);
      files.forEach(file => console.log(`   - ${file}`));
    }

    // Check for coverage reports
    const coverageDir = path.join(__dirname, 'coverage');
    const hasCoverage = await fs.access(coverageDir).then(() => true).catch(() => false);

    if (hasCoverage) {
      console.log('📈 Coverage report generated in ./coverage/');
    }

    // Git automation suggestions
    console.log('\n🔄 Git Commands for Results:');
    console.log('git add test_results/ coverage/');
    console.log('git commit -m "✅ Database QA tests completed - Day 3"');
    console.log('git push origin main');

  } catch (error) {
    console.error('❌ Error during test teardown:', error.message);
  }

  console.log('✅ Test environment teardown complete');
};