const io = require('socket.io-client');

console.log('🔍 Checking Engine Status...\n');

const engineSocket = io('http://localhost:3000/engine', {
  auth: { token: 'dev-bypass' }
});

engineSocket.on('connect', () => {
  console.log('✅ Engine namespace is CONNECTED');
  console.log(`   Socket ID: ${engineSocket.id}`);
  engineSocket.disconnect();
  process.exit(0);
});

engineSocket.on('connect_error', (err) => {
  console.log('❌ Engine namespace connection FAILED');
  console.log(`   Error: ${err.message}`);
  process.exit(1);
});

setTimeout(() => {
  if (!engineSocket.connected) {
    console.log('⚠️  Engine namespace NOT CONNECTED (timeout)');
    console.log('   This means no engine is running - jobs will queue');
    engineSocket.disconnect();
    process.exit(0);
  }
}, 3000);
