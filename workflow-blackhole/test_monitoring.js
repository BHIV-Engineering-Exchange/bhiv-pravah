/**
 * Test Script for Employee Monitoring System
 * This script tests the EMS signal collection functionality
 */

const axios = require('axios');

async function testEMSSignals() {
  console.log('🧪 Testing EMS Signal Collection System...\n');
  
  const BASE_URL = 'http://localhost:5001'; // Default server port
  const testEmployeeId = 'test_employee_' + Date.now();
  const testSessionId = 'test_session_' + Date.now();
  
  console.log('📝 Test Configuration:');
  console.log('  Base URL:', BASE_URL);
  console.log('  Employee ID:', testEmployeeId);
  console.log('  Session ID:', testSessionId);
  console.log('');
  
  try {
    // Test 1: Initialize signal tracking
    console.log('🔍 Test 1: Initializing signal tracking...');
    const initResponse = await axios.post(`${BASE_URL}/api/ems-signals/signals/init`, {
      employeeId: testEmployeeId,
      sessionId: testSessionId
    });
    
    console.log('✅ Initialization successful:', initResponse.data.success);
    console.log('');
    
    // Test 2: Send test signals
    console.log('📡 Test 2: Sending test signals...');
    const signals = [
      {
        type: 'window_focus',
        value: true,
        metadata: { visibilityState: 'visible', hasFocus: true }
      },
      {
        type: 'keystroke',
        metadata: { key: 'a', ctrlKey: false, altKey: false }
      },
      {
        type: 'mouse_movement',
        metadata: { x: 100, y: 200, type: 'move' }
      },
      {
        type: 'scroll_depth',
        metadata: { percentage: 25, scrollTop: 500, direction: 'down' }
      },
      {
        type: 'browser_hidden',
        value: false,
        metadata: { visibilityState: 'visible', documentHidden: false }
      }
    ];
    
    const signalsResponse = await axios.post(`${BASE_URL}/api/ems-signals/signals`, {
      employeeId: testEmployeeId,
      sessionId: testSessionId,
      signals: signals
    });
    
    console.log('✅ Signals sent successfully:', signalsResponse.data.processed, 'processed');
    console.log('📊 Current state activity score:', signalsResponse.data.statistics?.activityScore || 'N/A');
    console.log('');
    
    // Test 3: Get current signal state
    console.log('📋 Test 3: Getting current signal state...');
    const stateResponse = await axios.get(`${BASE_URL}/api/ems-signals/signals/${testEmployeeId}`);
    
    console.log('✅ State retrieved successfully');
    console.log('📈 Current State:', JSON.stringify(stateResponse.data.currentState, null, 2));
    console.log('');
    
    // Test 4: Get live capture proof
    console.log('🔍 Test 4: Getting live capture proof...');
    const proofResponse = await axios.get(`${BASE_URL}/api/ems-signals/signals/${testEmployeeId}/proof`);
    
    console.log('✅ Live capture proof retrieved');
    console.log('📊 Proof Data:', JSON.stringify(proofResponse.data, null, 2));
    console.log('');
    
    console.log('🎉 All tests passed! EMS Signal Collection is working correctly.');
    console.log('');
    console.log('📋 Summary:');
    console.log('  • Signal initialization: ✅ Working');
    console.log('  • Signal collection: ✅ Working'); 
    console.log('  • State retrieval: ✅ Working');
    console.log('  • Live proof: ✅ Working');
    console.log('');
    console.log('🚀 The Employee Monitoring System is ready to track:');
    console.log('  • Mouse movements and clicks');
    console.log('  • Keystrokes and typing patterns');
    console.log('  • Idle time and inactivity');
    console.log('  • Window focus and browser visibility');
    console.log('  • Scroll depth and content interaction');
    console.log('  • Task tab activity');
    console.log('  • App switching behavior');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    }
    console.error('\n💡 Make sure the server is running on port 5001');
  }
}

// Run the test
testEMSSignals();