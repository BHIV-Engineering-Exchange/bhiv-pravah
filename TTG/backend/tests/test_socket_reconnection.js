const io = require('socket.io-client');

console.log('🔌 SOCKET RECONNECTION LOGIC TEST\n');
console.log('='.repeat(70));

let connectionAttempts = 0;
let reconnectionAttempts = 0;
let connectionTimes = [];

const socket = io('http://localhost:3000', {
  autoConnect: true,
  transports: ['websocket'],
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 5000,
  auth: { token: 'test-token' }
});

socket.on('connect', () => {
  connectionAttempts++;
  connectionTimes.push(Date.now());
  console.log(`✅ Connected (attempt ${connectionAttempts})`);
  console.log(`   Socket ID: ${socket.id}`);
  console.log(`   Transport: ${socket.io.engine.transport.name}`);
});

socket.on('disconnect', (reason) => {
  console.log(`\n❌ Disconnected: ${reason}`);
});

socket.on('connect_error', (error) => {
  reconnectionAttempts++;
  console.log(`⚠️  Connection error (attempt ${reconnectionAttempts}): ${error.message}`);
});

socket.on('reconnect', (attemptNumber) => {
  console.log(`\n🔄 Reconnected after ${attemptNumber} attempts`);
});

socket.on('reconnect_attempt', (attemptNumber) => {
  console.log(`🔄 Reconnection attempt ${attemptNumber}...`);
});

socket.on('reconnect_failed', () => {
  console.log('\n❌ Reconnection failed - max attempts reached');
  
  console.log('\n' + '='.repeat(70));
  console.log('📊 RECONNECTION TEST SUMMARY');
  console.log('='.repeat(70));
  console.log(`Total connection attempts: ${connectionAttempts}`);
  console.log(`Total reconnection attempts: ${reconnectionAttempts}`);
  
  if (connectionTimes.length > 1) {
    console.log('\n⏱️  Backoff Timing:');
    for (let i = 1; i < connectionTimes.length; i++) {
      const delay = connectionTimes[i] - connectionTimes[i-1];
      console.log(`   Attempt ${i}: ${delay}ms delay`);
    }
  }
  
  console.log('\n✅ Expected behavior:');
  console.log('   - Exponential backoff (1s, 2s, 4s, 5s max)');
  console.log('   - Max 5 reconnection attempts');
  console.log('   - Connection state tracking');
  console.log('='.repeat(70));
  
  socket.close();
  process.exit(0);
});

// Test 1: Initial connection
console.log('\n1️⃣ TEST: Initial Connection');
console.log('Attempting to connect...\n');

// Test 2: Force disconnect after 3 seconds
setTimeout(() => {
  if (socket.connected) {
    console.log('\n2️⃣ TEST: Force Disconnect & Reconnection');
    console.log('Forcing disconnect...\n');
    socket.disconnect();
    
    // Reconnect after 1 second
    setTimeout(() => {
      console.log('Attempting reconnection...\n');
      socket.connect();
    }, 1000);
  }
}, 3000);

// Test 3: Summary after 15 seconds
setTimeout(() => {
  console.log('\n' + '='.repeat(70));
  console.log('📊 RECONNECTION TEST SUMMARY');
  console.log('='.repeat(70));
  console.log(`Connection state: ${socket.connected ? 'CONNECTED' : 'DISCONNECTED'}`);
  console.log(`Total connections: ${connectionAttempts}`);
  console.log(`Total reconnection attempts: ${reconnectionAttempts}`);
  
  if (connectionTimes.length > 1) {
    console.log('\n⏱️  Connection Timing:');
    for (let i = 1; i < connectionTimes.length; i++) {
      const delay = connectionTimes[i] - connectionTimes[i-1];
      console.log(`   Connection ${i}: ${delay}ms after previous`);
    }
  }
  
  console.log('\n✅ Reconnection Logic Verified:');
  console.log(`   ${connectionAttempts > 1 ? '✅' : '❌'} Multiple connections successful`);
  console.log(`   ${socket.connected ? '✅' : '❌'} Final state: connected`);
  console.log('='.repeat(70));
  
  socket.close();
  process.exit(0);
}, 15000);
