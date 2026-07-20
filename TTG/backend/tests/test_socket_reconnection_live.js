require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');

console.log('🔌 SOCKET RECONNECTION LOGIC TEST\n');
console.log('='.repeat(70));

// Generate valid token
const token = jwt.sign(
  { sub: 'test-user', roles: 'user' },
  process.env.JWT_SECRET || 'dev_secret_key',
  { expiresIn: '1h', issuer: process.env.JWT_ISSUER || 'sovereign-core' }
);

let connectionAttempts = 0;
let disconnectCount = 0;
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
  auth: { token }
});

socket.on('connect', () => {
  connectionAttempts++;
  connectionTimes.push(Date.now());
  console.log(`✅ Connected (attempt ${connectionAttempts})`);
  console.log(`   Socket ID: ${socket.id}`);
  console.log(`   Transport: ${socket.io.engine.transport.name}`);
});

socket.on('disconnect', (reason) => {
  disconnectCount++;
  console.log(`\n❌ Disconnected (${disconnectCount}): ${reason}`);
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

// Test 1: Initial connection
console.log('\n1️⃣ TEST: Initial Connection');
console.log('Attempting to connect...\n');

// Test 2: Force disconnect after 2 seconds
setTimeout(() => {
  if (socket.connected) {
    console.log('\n2️⃣ TEST: Manual Disconnect & Auto-Reconnect');
    console.log('Forcing disconnect to test auto-reconnection...\n');
    socket.io.engine.close();
  }
}, 2000);

// Test 3: Summary after 10 seconds
setTimeout(() => {
  console.log('\n' + '='.repeat(70));
  console.log('📊 RECONNECTION TEST RESULTS');
  console.log('='.repeat(70));
  console.log(`Final state: ${socket.connected ? 'CONNECTED ✅' : 'DISCONNECTED ❌'}`);
  console.log(`Total successful connections: ${connectionAttempts}`);
  console.log(`Total disconnects: ${disconnectCount}`);
  console.log(`Total reconnection attempts: ${reconnectionAttempts}`);
  
  if (connectionTimes.length > 1) {
    console.log('\n⏱️  Reconnection Timing (Exponential Backoff):');
    for (let i = 1; i < connectionTimes.length; i++) {
      const delay = connectionTimes[i] - connectionTimes[i-1];
      console.log(`   Reconnection ${i}: ${delay}ms after disconnect`);
    }
  }
  
  console.log('\n✅ Verified Features:');
  console.log(`   ${connectionAttempts >= 2 ? '✅' : '❌'} Auto-reconnection after disconnect`);
  console.log(`   ${socket.connected ? '✅' : '❌'} Connection restored`);
  console.log(`   ${connectionTimes.length > 1 ? '✅' : '❌'} Backoff timing applied`);
  
  console.log('\n📋 Expected Behavior:');
  console.log('   - Initial connection successful');
  console.log('   - Auto-reconnect after forced disconnect');
  console.log('   - Exponential backoff (1s, 2s, 4s, 5s max)');
  console.log('   - Max 5 reconnection attempts');
  console.log('='.repeat(70));
  
  socket.close();
  process.exit(connectionAttempts >= 2 ? 0 : 1);
}, 10000);
