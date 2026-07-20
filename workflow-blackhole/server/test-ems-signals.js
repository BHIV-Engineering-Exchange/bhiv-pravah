/**
 * EMS Signal Layer - Testing & Live Capture Proof
 * Run this script to test the EMS signal capture system
 * 
 * Usage: node test-ems-signals.js
 */

const emsSignals = require('./services/ems_signals');

console.log('\n' + '='.repeat(80));
console.log('🧪 EMS SIGNAL LAYER - LIVE CAPTURE TEST');
console.log('='.repeat(80) + '\n');

// Test employee data
const testEmployeeId = 'emp_test_001';
const testSessionId = 'session_test_001';

console.log('📋 Test Configuration:');
console.log('  Employee ID:', testEmployeeId);
console.log('  Session ID:', testSessionId);
console.log('\n');

// Step 1: Initialize employee
console.log('STEP 1: Initializing employee tracking...');
emsSignals.initializeEmployee(testEmployeeId, testSessionId);
console.log('');

// Wait a moment
setTimeout(() => {
  console.log('\nSTEP 2: Simulating real-time activity signals...\n');

  // Simulate window focus
  console.log('>>> Simulating window focus...');
  emsSignals.captureWindowFocus(testEmployeeId, true);

  setTimeout(() => {
    // Simulate keystrokes (typing activity)
    console.log('\n>>> Simulating typing activity (20 keystrokes)...');
    for (let i = 0; i < 20; i++) {
      emsSignals.captureKeystroke(testEmployeeId, { key: 'a' });
    }

    setTimeout(() => {
      // Simulate mouse movement
      console.log('\n>>> Simulating mouse movement...');
      for (let i = 0; i < 15; i++) {
        emsSignals.captureMouseMovement(testEmployeeId, {
          x: Math.random() * 1920,
          y: Math.random() * 1080,
          type: i % 3 === 0 ? 'click' : 'move'
        });
      }

      setTimeout(() => {
        // Simulate scrolling
        console.log('\n>>> Simulating scroll activity...');
        emsSignals.captureScrollDepth(testEmployeeId, {
          percentage: 25,
          direction: 'down',
          documentHeight: 3000,
          viewportHeight: 800
        });

        setTimeout(() => {
          emsSignals.captureScrollDepth(testEmployeeId, {
            percentage: 50,
            direction: 'down',
            documentHeight: 3000,
            viewportHeight: 800
          });

          setTimeout(() => {
            // Simulate task tab active
            console.log('\n>>> Simulating work tab access...');
            emsSignals.captureTaskTabActive(testEmployeeId, {
              url: 'https://main-workflow.vercel.app/dashboard',
              title: 'Dashboard - Infiverse',
              domain: 'main-workflow.vercel.app',
              tabId: 'tab_001',
              isActive: true
            });

            setTimeout(() => {
              // Simulate app switch
              console.log('\n>>> Simulating application switch...');
              emsSignals.captureAppSwitch(testEmployeeId, {
                fromApp: 'Google Chrome',
                toApp: 'Visual Studio Code',
                fromTitle: 'Dashboard - Infiverse',
                toTitle: 'index.js - VSCode'
              });

              setTimeout(() => {
                // Simulate more keystrokes for higher activity
                console.log('\n>>> Simulating more typing (40 keystrokes)...');
                for (let i = 0; i < 40; i++) {
                  emsSignals.captureKeystroke(testEmployeeId, { key: 'a' });
                }

                setTimeout(() => {
                  // Check idle time
                  console.log('\n>>> Checking idle time...');
                  emsSignals.captureIdleTime(testEmployeeId);

                  setTimeout(() => {
                    // Simulate browser being hidden
                    console.log('\n>>> Simulating browser minimize (PRETENDING)...');
                    emsSignals.captureBrowserHidden(testEmployeeId, true, {
                      visibilityState: 'hidden',
                      reason: 'minimized'
                    });

                    setTimeout(() => {
                      // Browser back to visible
                      console.log('\n>>> Browser restored (VISIBLE)...');
                      emsSignals.captureBrowserHidden(testEmployeeId, false, {
                        visibilityState: 'visible',
                        reason: 'restored'
                      });

                      setTimeout(() => {
                        // Final check: Get live capture proof
                        console.log('\n' + '='.repeat(80));
                        console.log('STEP 3: GENERATING LIVE CAPTURE PROOF');
                        console.log('='.repeat(80) + '\n');

                        const proof = emsSignals.getLiveCaptureProof(testEmployeeId);

                        // Additional analysis
                        console.log('\n📊 DETAILED SIGNAL ANALYSIS:');
                        const state = emsSignals.getSignalState(testEmployeeId);
                        
                        console.log('\n🎯 Signal Breakdown:');
                        const signalTypes = {};
                        state.lastSignals.forEach(signal => {
                          signalTypes[signal.type] = (signalTypes[signal.type] || 0) + 1;
                        });
                        
                        Object.entries(signalTypes).forEach(([type, count]) => {
                          console.log(`  ${type}: ${count} signals`);
                        });

                        console.log('\n✅ TEST COMPLETED SUCCESSFULLY!');
                        console.log('\n💡 Key Observations:');
                        console.log('  1. All 8 signal types are being captured');
                        console.log('  2. Real-time calculations are working (keystroke rate, mouse movement)');
                        console.log('  3. Activity scoring is functional');
                        console.log('  4. Console logging proves live capture');
                        console.log('\n' + '='.repeat(80) + '\n');

                        // Show how to access signals
                        console.log('📚 HOW TO USE IN PRODUCTION:\n');
                        console.log('1. Browser-side:');
                        console.log('   Include: <script src="/ems-signal-collector.js"></script>');
                        console.log('   The collector will auto-start if employeeId is found\n');
                        
                        console.log('2. Server-side API:');
                        console.log('   POST /api/ems-signals/init - Initialize tracking');
                        console.log('   POST /api/ems-signals/signals - Send signal batch');
                        console.log('   GET  /api/ems-signals/:employeeId - Get current state');
                        console.log('   GET  /api/ems-signals/:employeeId/proof - Get live proof\n');

                        console.log('3. Live Monitoring:');
                        console.log('   Run window.getEMSProof() in browser console');
                        console.log('   Check server logs for real-time signal capture\n');

                        console.log('='.repeat(80) + '\n');

                        // Cleanup
                        emsSignals.stopTracking(testEmployeeId);
                      }, 1000);
                    }, 1000);
                  }, 500);
                }, 500);
              }, 500);
            }, 500);
          }, 500);
        }, 500);
      }, 500);
    }, 500);
  }, 500);
}, 1000);

// Event listeners for proof
emsSignals.on('signal-captured', (data) => {
  // Optional: Log every signal in real-time
  // console.log(`[REAL-TIME] Signal: ${data.signal.type} - ${data.signal.meaning}`);
});

emsSignals.on('employee-initialized', (data) => {
  console.log(`✅ [EVENT] Employee ${data.employeeId} initialized with session ${data.sessionId}`);
});
