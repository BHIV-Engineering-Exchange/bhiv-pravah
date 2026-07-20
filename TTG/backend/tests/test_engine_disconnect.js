require('dotenv').config();
const io = require('socket.io-client');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const ENGINE_SHARED_SECRET = process.env.ENGINE_SHARED_SECRET;
const JWT_SECRET = process.env.JWT_SECRET;

const engineToken = jwt.sign(
  { engineId: 'test_disconnect', role: 'engine' },
  JWT_SECRET,
  { expiresIn: '1h' }
);

console.log('🧪 Test: Engine Disconnect Simulation\n');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});

function signMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts = Date.now();
  const sig = crypto
    .createHmac('sha256', ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  return { payload, nonce, ts, sig };
}

let jobCount = 0;

socket.on('connect', () => {
  console.log('✅ Engine connected\n');
  socket.emit('engine_ready');
  
  const heartbeat = setInterval(() => {
    socket.emit('engine_heartbeat');
  }, 3000);
  
  // Simulate disconnect after 8 seconds
  setTimeout(() => {
    console.log('\n⚠️  Simulating engine disconnect...\n');
    clearInterval(heartbeat);
    socket.disconnect();
    
    // Reconnect after 5 seconds
    setTimeout(() => {
      console.log('🔄 Attempting reconnect...\n');
      const newSocket = io('http://localhost:3000/engine', {
        auth: { token: engineToken }
      });
      
      newSocket.on('connect', () => {
        console.log('✅ Engine reconnected!\n');
        newSocket.emit('engine_ready');
        
        setTimeout(() => {
          console.log('✅ Disconnect test complete!\n');
          newSocket.disconnect();
          process.exit(0);
        }, 3000);
      });
    }, 5000);
  }, 8000);
});

socket.on('engine_job', (job) => {
  jobCount++;
  console.log(`📦 Job ${jobCount} received: ${job.job_id}`);
  
  const jobId = job.job_id;
  
  socket.emit('job_ack', signMessage({ jobId, status: 'received' }));
  
  setTimeout(() => {
    socket.emit('job_started', signMessage({ job_id: jobId, timestamp: Date.now() }));
    console.log(`  ✅ Job ${jobCount} started`);
  }, 500);
  
  setTimeout(() => {
    socket.emit('job_completed', signMessage({ 
      job_id: jobId, 
      result: { success: true },
      timestamp: Date.now() 
    }));
    console.log(`  ✅ Job ${jobCount} completed\n`);
  }, 1500);
});

socket.on('ready_ack', () => console.log('✅ Ready acknowledged\n'));
socket.on('heartbeat_ack', () => console.log('💓 Heartbeat'));

socket.on('disconnect', () => {
  console.log('❌ Engine disconnected\n');
});

console.log('Waiting for jobs...\n');
console.log('Engine will disconnect after 8 seconds\n');
