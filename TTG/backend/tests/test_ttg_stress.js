/**
 * TTG Stress Test v2 - Enhanced Validation
 * Tests: Determinism, Comprehensive Input Validation, High-Frequency
 */

const { validateTTGInput } = require('./ttg_integration/validator');
const { textToSchema } = require('./intent-layer');

console.log('🧪 TTG Stress Test Suite v2\n');

// ============================================
// TEST 1: Determinism - Same Input 5 Times
// ============================================
console.log('📊 TEST 1: Determinism Check');
console.log('─'.repeat(50));

const testInput = "Make a fast runner with jump and obstacles";
const results = [];

for (let i = 1; i <= 5; i++) {
  const result = textToSchema(testInput);
  results.push(JSON.stringify(result.schema));
  console.log(`Run ${i}: ${result.success ? '✅' : '❌'}`);
}

const allIdentical = results.every(r => r === results[0]);
console.log(`\n🎯 Result: ${allIdentical ? '✅ PASS - All schemas identical' : '❌ FAIL - Schemas differ'}\n`);

// ============================================
// TEST 2: Comprehensive Input Validation
// ============================================
console.log('\n📊 TEST 2: Comprehensive Input Validation');
console.log('─'.repeat(50));

const malformedInputs = [
  { input: '', name: 'Empty string' },
  { input: '   ', name: 'Whitespace only' },
  { input: 'a'.repeat(501), name: 'Too long (>500)' },
  { input: '!@#$%^&*()', name: 'Only special chars' },
  { input: '<script>alert("xss")</script>', name: 'XSS attempt' },
  { input: 'null', name: 'Reserved word: null' },
  { input: 'undefined', name: 'Reserved word: undefined' },
  { input: '{"json": "object"}', name: 'JSON object' },
  { input: '\n\n\n', name: 'Only newlines' },
  { input: '🎮🎮🎮', name: 'Only emojis' }
];

let safeRejections = 0;
malformedInputs.forEach((test, i) => {
  const result = validateTTGInput(test.input);
  const status = result.valid ? '❌ Accepted' : '✅ Rejected';
  console.log(`${i + 1}. ${test.name}: ${status}`);
  if (!result.valid) safeRejections++;
});

console.log(`\n🎯 Result: ${safeRejections}/${malformedInputs.length} safely rejected`);
console.log(`${safeRejections === 10 ? '✅ PERFECT SCORE!' : '⚠️ Needs improvement'}\n`);

// ============================================
// TEST 3: High-Frequency Dispatch
// ============================================
console.log('\n📊 TEST 3: High-Frequency Dispatch');
console.log('─'.repeat(50));

const testPrompts = [
  "fast runner",
  "easy platformer",
  "hard arena game",
  "slow runner with obstacles",
  "medium difficulty side scroller"
];

let successCount = 0;
let errorCount = 0;
const startTime = Date.now();

for (let i = 0; i < 100; i++) {
  try {
    const prompt = testPrompts[i % testPrompts.length];
    const result = textToSchema(prompt);
    if (result.success) successCount++;
    else errorCount++;
  } catch (err) {
    errorCount++;
  }
}

const duration = Date.now() - startTime;
const throughput = (100 / duration * 1000).toFixed(2);

console.log(`Processed: 100 requests`);
console.log(`Success: ${successCount}`);
console.log(`Errors: ${errorCount}`);
console.log(`Duration: ${duration}ms`);
console.log(`Throughput: ${throughput} req/sec`);
console.log(`\n🎯 Result: ${errorCount === 0 ? '✅ PASS - No crashes' : '❌ FAIL - Errors occurred'}\n`);

// ============================================
// SUMMARY
// ============================================
console.log('\n📋 STRESS TEST SUMMARY v2');
console.log('═'.repeat(50));
console.log(`✅ Determinism: ${allIdentical ? 'PASS' : 'FAIL'}`);
console.log(`✅ Input Validation: ${safeRejections}/10 rejected ${safeRejections === 10 ? '(PERFECT!)' : ''}`);
console.log(`✅ High-Frequency: ${errorCount === 0 ? 'PASS' : 'FAIL'} (${throughput} req/sec)`);
console.log('═'.repeat(50));

if (allIdentical && safeRejections === 10 && errorCount === 0) {
  console.log('\n🎉 ALL TESTS PASSED - 10/10 VALIDATION SCORE!\n');
} else {
  console.log('\n⚠️ Some tests need attention\n');
}
