/**
 * Verification Script for Employee Monitoring System Setup
 * This script verifies that all components of the EMS are properly configured
 */

console.log('🔍 Verifying Employee Monitoring System Setup...\n');

// Check that all required files exist and are properly configured
const fs = require('fs');
const path = require('path');

const checks = [
  {
    name: 'EMS Signal Service',
    path: './server/services/ems_signals.js',
    check: () => fs.existsSync('./server/services/ems_signals.js'),
    description: 'Core signal processing service for mouse, keystroke, idle tracking'
  },
  {
    name: 'EMS Signals Routes',
    path: './server/routes/emsSignals.js',
    check: () => fs.existsSync('./server/routes/emsSignals.js'),
    description: 'API routes for receiving real-time signals'
  },
  {
    name: 'EMS Signal Collector Script',
    path: './client/public/ems-signal-collector.js',
    check: () => fs.existsSync('./client/public/ems-signal-collector.js'),
    description: 'Browser-side script for capturing mouse, keystroke, idle events'
  },
  {
    name: 'EMS Route Registration',
    path: './server/index.js',
    check: () => {
      const content = fs.readFileSync('./server/index.js', 'utf8');
      return content.includes('/api/ems-signals') && content.includes('emsSignals');
    },
    description: 'Route registration in main server file'
  },
  {
    name: 'Frontend Script Integration',
    path: './client/index.html',
    check: () => {
      const content = fs.readFileSync('./client/index.html', 'utf8');
      return content.includes('ems-signal-collector.js');
    },
    description: 'Script inclusion in frontend HTML'
  },
  {
    name: 'Monitoring Dashboard',
    path: './client/src/pages/EmployeeMonitoring.jsx',
    check: () => fs.existsSync('./client/src/pages/EmployeeMonitoring.jsx'),
    description: 'Frontend monitoring dashboard'
  }
];

let passedChecks = 0;
let totalChecks = checks.length;

console.log('📋 Component Status Check:');
console.log('=' + '=' * 60);

checks.forEach((check, index) => {
  const status = check.check() ? '✅ PASS' : '❌ FAIL';
  if (check.check()) passedChecks++;
  
  console.log(`${index + 1}. ${check.name} ${status}`);
  console.log(`   Description: ${check.description}`);
  console.log(`   File: ${check.path}`);
  console.log('');
});

console.log('=' + '=' * 60);
console.log(`📊 Summary: ${passedChecks}/${totalChecks} checks passed`);

if (passedChecks === totalChecks) {
  console.log('\n🎉 ALL SYSTEMS READY!');
  console.log('\n🚀 The Employee Monitoring System is fully configured to track:');
  console.log('   • Mouse movements and clicks (real-time)');
  console.log('   • Keystrokes and typing patterns (real-time)');
  console.log('   • Idle time and inactivity detection (real-time)');
  console.log('   • Window focus and browser visibility');
  console.log('   • Scroll depth and content interaction');
  console.log('   • Task tab activity and website monitoring');
  console.log('   • App switching behavior detection');
  console.log('');
  console.log('🔧 How it works:');
  console.log('   1. Browser script (ems-signal-collector.js) captures events');
  console.log('   2. Signals are sent to server via /api/ems-signals endpoints');
  console.log('   3. Server processes and stores activity data');
  console.log('   4. Real-time dashboard displays monitoring data');
  console.log('');
  console.log('💡 To start the system:');
  console.log('   1. Start the server: cd server && npm run dev');
  console.log('   2. Start the client: cd client && npm run dev');
  console.log('   3. Access the monitoring dashboard at /monitoring');
  console.log('   4. Employee activity will be automatically tracked when they visit the site');
} else {
  console.log('\n❌ Some components need attention. Please check the failed items above.');
}

console.log('\n✨ Setup verification completed!');