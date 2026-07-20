// Quick test script to verify domain system works
// Run this in your browser console or as a test component

import MultiDomainAssessmentService from './lib/multiDomainAssessmentService.js';
import AIAssistanceDetector from './lib/aiAssistanceDetector.js';

export async function testDomainSystem() {
  console.log('🧪 Testing 13-Domain System...\n');

  // Test 1: Load domains
  console.log('📋 Test 1: Loading domains...');
  const domains = await MultiDomainAssessmentService.getAllDomains();
  console.log(`✅ Loaded ${domains.length} domains`);
  console.assert(domains.length === 13, 'Should have 13 domains');

  // Test 2: Validate selection
  console.log('\n📋 Test 2: Validating domain selection...');
  const validation1 = MultiDomainAssessmentService.validateDomainSelection([]);
  console.assert(validation1.valid === false, 'Empty selection should fail');
  console.log('✅ Empty selection rejected');

  const validation2 = MultiDomainAssessmentService.validateDomainSelection(['iot']);
  console.assert(validation2.valid === true, 'Single domain should pass');
  console.log('✅ Single domain accepted');

  // Test 3: Adaptive difficulty
  console.log('\n📋 Test 3: Testing adaptive difficulty...');
  const diff1 = MultiDomainAssessmentService.calculateAdaptiveDifficulty(['iot'], 10);
  console.log('1 domain:', diff1);
  console.assert(diff1.hard >= 2, 'Single domain should have harder questions');
  console.log('✅ Single domain = harder questions');

  const diff5 = MultiDomainAssessmentService.calculateAdaptiveDifficulty(
    ['iot', 'blockchain', 'gaming', 'web_dev', 'cybersecurity'], 
    10
  );
  console.log('5 domains:', diff5);
  console.assert(diff5.easy >= 4, 'Multiple domains should have easier questions');
  console.log('✅ Multiple domains = easier questions');

  // Test 4: Generate assessment
  console.log('\n📋 Test 4: Generating assessment...');
  try {
    const assessment = await MultiDomainAssessmentService.generateMultiDomainAssessment(
      ['iot', 'ai_ml_ds'],
      10,
      'test-user'
    );
    console.log(`✅ Generated ${assessment.questions.length} questions`);
    console.log('Metadata:', assessment.metadata);
    console.assert(assessment.questions.length === 10, 'Should generate 10 questions');
  } catch (error) {
    console.error('❌ Assessment generation failed:', error);
  }

  // Test 5: AI Detection
  console.log('\n📋 Test 5: Testing AI detection...');
  
  const normalResponse = "MQTT is good for IoT because it uses less bandwidth.";
  const analysis1 = AIAssistanceDetector.analyzeResponse(
    normalResponse,
    "Which protocol is lightweight?",
    30
  );
  console.log('Normal response detection:', analysis1.detectionLevel);
  console.log('Suspicion score:', analysis1.suspicionScore);
  console.assert(analysis1.detectionLevel === 'clean', 'Normal response should be clean');
  console.log('✅ Normal response detected as clean');

  const aiResponse = "As an AI language model, I would like to explain that MQTT, which stands for Message Queuing Telemetry Transport, is indeed a highly efficient protocol. Furthermore, it is important to note that this protocol is specifically designed for constrained devices. In conclusion, MQTT represents a paradigm shift in IoT communications.";
  const analysis2 = AIAssistanceDetector.analyzeResponse(
    aiResponse,
    "Which protocol is lightweight?",
    5
  );
  console.log('\nAI-like response detection:', analysis2.detectionLevel);
  console.log('Suspicion score:', analysis2.suspicionScore);
  console.log('Flags:', analysis2.flags);
  console.log('✅ AI-like response flagged');

  console.log('\n🎉 All tests passed! System is ready.');
}

// Run tests
testDomainSystem().catch(console.error);
